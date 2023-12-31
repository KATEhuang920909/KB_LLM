# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     tt
   Author :       huangkai
   date：          2023/10/10
-------------------------------------------------
"""
# -*- coding:utf-8 -*-
# @project: ChatGPT
# @filename: train
# @author: 刘聪NLP
# @zhihu: https://www.zhihu.com/people/LiuCongNLP
# @contact: logcongcong@gmail.com
# @time: 2023/8/6 16:13
"""
    文件说明：

"""
import argparse
import json
import math
from tqdm import tqdm
import torch
from torch.utils.data import DataLoader, RandomSampler
from torch.utils.data.distributed import DistributedSampler
import deepspeed
from utils import print_trainable_parameters, print_rank_0, to_device, set_random_seed, save_model
from utils import DataCollator
from peft import LoraConfig, get_peft_model
from model import MODE

try:
    from torch.utils.tensorboard import SummaryWriter
except ImportError:
    from tensorboard import SummaryWriter


def parse_args():
    parser = argparse.ArgumentParser()
    # Model
    parser.add_argument("--model_name_or_path", type=str, help="", required=True)
    # DataSet
    parser.add_argument("--train_path", default="", type=str, help="")
    parser.add_argument("--dev_path", default="", type=str, help="")
    parser.add_argument("--max_len", type=int, default=1024, help="")
    parser.add_argument("--max_src_len", type=int, default=256, help="")
    parser.add_argument("--is_skip", action='store_true', help="")
    # Train
    parser.add_argument("--per_device_train_batch_size", type=int, default=16, help="")
    parser.add_argument("--learning_rate", type=float, default=1e-3, help="")
    parser.add_argument("--weight_decay", type=float, default=0.1, help="")
    parser.add_argument("--num_train_epochs", type=int, default=1, help="")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=1, help="")
    parser.add_argument("--warmup_ratio", type=float, default=0.1, help="")
    parser.add_argument("--output_dir", type=str, default=None, help="")
    parser.add_argument("--mode", type=str, default="glm2", help="")
    parser.add_argument("--train_type", type=str, default="lora", help="")
    parser.add_argument("--seed", type=int, default=1234, help="")
    parser.add_argument("--local_rank", type=int, default=-1, help="")
    parser.add_argument("--show_loss_step", default=10, type=int, help="")
    parser.add_argument("--gradient_checkpointing", action='store_true', help="")
    parser.add_argument("--save_model_step", default=None, type=int, help="")
    # deepspeed features
    parser.add_argument("--ds_file", type=str, default="ds_zero2.json", help="")
    # LoRA
    parser.add_argument("--lora_dim", type=int, default=8, help="")
    parser.add_argument("--lora_alpha", type=int, default=30, help="")
    parser.add_argument("--lora_dropout", type=float, default=0.1, help="")
    parser.add_argument("--lora_module_name", type=str, default="query_key_value", help="")
    # Freeze
    parser.add_argument("--freeze_module_name", type=str, default="layers.27.", help="")
    # P-tuning
    parser.add_argument('--pre_seq_len', type=int, default=16, help='')
    parser.add_argument('--prefix_projection', type=bool, default=True, help='')
    parser = deepspeed.add_config_arguments(parser)
    return parser.parse_args()


def evaluate(dev_path):
    infer_model = deepspeed.init_inference(model,
                                         mp_size=2,
                                         dtype=torch.half,
                                         replace_with_kernel_inject=True)
    infer_model.eval()
    with torch.no_grad():
        sums, count = 0.0, 0.0
        max_tgt_len = args.max_len - args.max_src_len - 3
        with open(dev_path, "r", encoding="utf-8") as fh:
            data = fh.readlines()
            for i, line in enumerate(tqdm(data, desc="iter")):
                with torch.no_grad():
                    sample = json.loads(line.strip())
                    if sample["task_type"] == "tuple_extract":
                        prompt = "请抽取下面问句的主宾二元组，格式xx|xx。问句："
                        src_tokens = tokenizer.tokenize(prompt + sample["question"])
                    elif sample["task_type"] == "table_extract":
                        prompt = "已知下面表格信息："
                        src_tokens = tokenizer.tokenize(
                            prompt + "{}，\n问：{}\n答：".format(sample["instruction"], sample["question"]))

                    if len(src_tokens) > args.max_src_len:
                        # 当输入内容超长时，随向后截断，但保留“\n答：”内容
                        src_tokens = src_tokens[:args.max_src_len - 3] + src_tokens[-3:]
                        skip_flag = True

                    # max_tgt_len = max_len - 3 - len(src_tokens)
                    tgt_tokens = tokenizer.tokenize(sample["answer"])

                    if len(tgt_tokens) > max_tgt_len:
                        tgt_tokens = tgt_tokens[:max_tgt_len]
                        skip_flag = True

                    # ChatGLM需要在输入内容后面增加"[gMASK]"、"<sop>"标记
                    tokens = src_tokens + ["[gMASK]", "<sop>"] + tgt_tokens + ["<eop>"]
                    input_ids = tokenizer.convert_tokens_to_ids(tokens)
                    # input_ids = tokenizer.encode("帮我写个快排算法")

                    input_ids = torch.tensor(input_ids).to("cuda:{}".format(0))
                    generation_kwargs = {
                        "min_length": 1,
                        "max_new_tokens": max_tgt_len,
                        "top_p": 0.7,
                        "temperature": 0.95,
                        "do_sample": False,
                        "num_return_sequences": 1,
                    }
                    # print(input_ids)
                    response = generate(input_ids)

                    sums += 1
                    for i_r in range(generation_kwargs["num_return_sequences"]):
                        outputs = response.tolist()[i_r][input_ids.shape[1]:]
                        pre_res = tokenizer.decode(outputs).replace("<eop>", "")
                        real_res = sample["answer"]
                        if pre_res == real_res:
                            count += 1

    return count / sums


if __name__ == "__main__":
    args = parse_args()
    if args.local_rank == -1:
        device = torch.device("cuda")
    else:
        torch.cuda.set_device(args.local_rank)
        device = torch.device("cuda", args.local_rank)
        deepspeed.init_distributed()
    args.global_rank = torch.distributed.get_rank()

    with open(args.ds_file, "r", encoding="utf-8") as fh:
        ds_config = json.load(fh)

    ds_config['train_micro_batch_size_per_gpu'] = args.per_device_train_batch_size
    ds_config[
        'train_batch_size'] = args.per_device_train_batch_size * torch.distributed.get_world_size() * args.gradient_accumulation_steps
    ds_config['gradient_accumulation_steps'] = args.gradient_accumulation_steps

    if args.global_rank <= 0:
        tb_write = SummaryWriter()

    set_random_seed(args.seed)
    torch.distributed.barrier()
    # load tokenizer
    tokenizer = MODE[args.mode]["tokenizer"].from_pretrained(args.model_name_or_path)
    print_rank_0("tokenizer.pad_token: {}".format(tokenizer.pad_token), args.global_rank)
    print_rank_0("tokenizer.eos_token: {}".format(tokenizer.eos_token), args.global_rank)

    # load model
    if args.train_type == "lora":
        model = MODE[args.mode]["model"].from_pretrained(args.model_name_or_path)
        lora_module_name = args.lora_module_name.split(",")
        config = LoraConfig(r=args.lora_dim,
                            lora_alpha=args.lora_alpha,
                            target_modules=lora_module_name,
                            lora_dropout=args.lora_dropout,
                            bias="none",
                            task_type="CAUSAL_LM",
                            inference_mode=False,
                            )
        model = get_peft_model(model, config)
        model.config.torch_dtype = torch.float32
    elif args.train_type == "freeze":
        model = MODE[args.mode]["model"].from_pretrained(args.model_name_or_path)
        freeze_module_name = args.freeze_module_name.split(",")
        for name, param in model.named_parameters():
            if not any(nd in name for nd in freeze_module_name):
                param.requires_grad = False
    elif args.train_type == "ptuning":
        config = MODE[args.mode]["config"].from_pretrained(args.model_name_or_path)
        config.pre_seq_len = args.pre_seq_len
        config.prefix_projection = args.prefix_projection
        model = MODE[args.mode]["model"].from_pretrained(args.model_name_or_path, config=config)
        for name, param in model.named_parameters():
            if not any(nd in name for nd in ["prefix_encoder"]):
                param.requires_grad = False
    elif args.train_type == "all":
        model = MODE[args.mode]["model"].from_pretrained(args.model_name_or_path)
    else:
        raise Exception("train_type无效")

    # load data
    train_dataset = MODE[args.mode]["dataset"](args.train_path, tokenizer, args.max_len, args.max_src_len, args.is_skip)
    if args.local_rank == -1:
        train_sampler = RandomSampler(train_dataset)
    else:
        train_sampler = DistributedSampler(train_dataset)

    data_collator = DataCollator(tokenizer)
    train_dataloader = DataLoader(train_dataset, collate_fn=data_collator, sampler=train_sampler,
                                  batch_size=args.per_device_train_batch_size)
    print_rank_0("len(train_dataloader) = {}".format(len(train_dataloader)), args.global_rank)
    print_rank_0("len(train_dataset) = {}".format(len(train_dataset)), args.global_rank)
    # load optimizer
    ds_config["optimizer"]["params"]["lr"] = args.learning_rate
    ds_config["optimizer"]["params"]["betas"] = (0.9, 0.95)
    ds_config["optimizer"]["params"]["eps"] = 1e-8
    ds_config["optimizer"]["params"]["weight_decay"] = 0.1
    num_training_steps = args.num_train_epochs * math.ceil(len(train_dataloader) / args.gradient_accumulation_steps)
    print_rank_0("num_training_steps = {}".format(num_training_steps), args.global_rank)
    num_warmup_steps = int(args.warmup_ratio * num_training_steps)
    print_rank_0("num_warmup_steps = {}".format(num_warmup_steps), args.global_rank)
    ds_config["scheduler"]["params"]["total_num_steps"] = num_training_steps
    ds_config["scheduler"]["params"]["warmup_num_steps"] = num_warmup_steps
    ds_config["scheduler"]["params"]["warmup_max_lr"] = args.learning_rate
    ds_config["scheduler"]["params"]["warmup_min_lr"] = args.learning_rate * 0.1

    # print parameters
    for name, param in model.named_parameters():
        if param.requires_grad == True:
            print_rank_0(name, 0)
    print_trainable_parameters(model)

    # gradient_checkpointing
    if args.gradient_checkpointing:
        model.gradient_checkpointing_enable()
        if hasattr(model, "enable_input_require_grads"):
            model.enable_input_require_grads()
        else:
            def make_inputs_require_grad(module, input, output):
                output.requires_grad_(True)


            model.get_input_embeddings().register_forward_hook(make_inputs_require_grad)

    # init deepspeed
    model, optimizer, _, lr_scheduler = deepspeed.initialize(model=model, args=args, config=ds_config,
                                                             dist_init_required=True)
    tr_loss, logging_loss, min_loss, best_acc = 0.0, 0.0, 0.0, 0.0
    global_step = 0
    # train
    for epoch in range(args.num_train_epochs):
        print_rank_0("Beginning of Epoch {}/{}, Total Micro Batches {}".format(epoch + 1, args.num_train_epochs,
                                                                               len(train_dataloader)), args.global_rank)
        model.train()
        for step, batch in enumerate(train_dataloader):
            batch = to_device(batch, device)
            # print(batch["input_ids"].shape)
            outputs = model(**batch, use_cache=False)
            loss = outputs.loss
            tr_loss += loss.item()
            model.backward(loss)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            model.step()
            if (step + 1) % args.gradient_accumulation_steps == 0:
                global_step += 1
                # write loss
                if global_step % args.show_loss_step == 0:
                    print_rank_0("Epoch: {}, step: {}, global_step:{}, loss: {}".format(epoch, step + 1, global_step,
                                                                                        (tr_loss - logging_loss) / (
                                                                                                args.show_loss_step * args.gradient_accumulation_steps)),
                                 args.global_rank)
                    print_rank_0("step: {}-{}-{}".format(step + 1, global_step, model.global_steps), args.global_rank)
                    if args.global_rank <= 0:
                        tb_write.add_scalar("train_loss", (tr_loss - logging_loss) / (
                                args.show_loss_step * args.gradient_accumulation_steps), global_step)
                        logging_loss = tr_loss
                # save model
                if args.save_model_step is not None and global_step % args.save_model_step == 0:
                    # 若zero3训练，模型参数需要合并保存
                    if ds_config["zero_optimization"]["stage"] == 3:
                        state_dict = model._zero3_consolidated_16bit_state_dict()
                        if args.global_rank <= 0:
                            save_model(model, tokenizer, args.output_dir, f"epoch-{epoch + 1}-step-{global_step}",
                                       state_dict)
                    else:
                        if args.global_rank <= 0:
                            save_model(model, tokenizer, args.output_dir, f"epoch-{epoch + 1}-step-{global_step}")
                    model.train()
        acc = evaluate(args.dev_path)
        if acc > best_acc:
            best_acc = acc
            if ds_config["zero_optimization"]["stage"] == 3:
                state_dict = model._zero3_consolidated_16bit_state_dict()
                if args.global_rank <= 0:
                    acc_score = open(args.output_dir + "/acc_score.txt", "w")
                    acc_score.write(str(best_acc))
                    save_model(model, tokenizer, args.output_dir, "best_model", state_dict)
            else:
                if args.global_rank <= 0:
                    acc_score = open(args.output_dir + "/acc_score.txt", "w")
                    acc_score.write(str(best_acc))
                    save_model(model, tokenizer, args.output_dir, "best_model")
        print(f"epoch: {epoch} ,acc: {acc} ,best_acc:{best_acc}")
