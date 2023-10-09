# CUDA_VISIBLE_DEVICES=0 deepspeed --master_port 520 train.py \
# --train_path /root/autodl-tmp/KB_LLM/data/train_sft.json \
# --model_name_or_path /root/autodl-tmp/ptms/THUDM-chatglm-6b/ \
# --per_device_train_batch_size 1 \
# --max_len 1560 \
# --max_src_len 1124 \
# --learning_rate 1e-4 \
# --weight_decay 0.1 \
# --num_train_epochs 10 \
# --gradient_accumulation_steps 4 \
# --warmup_ratio 0.1 \
# --mode glm \
# --train_type freeze \
# --freeze_module_name "layers.27.,layers.26.,layers.25.,layers.24." \
# --seed 1234 \
# --ds_file ds_zero2_no_offload.json \
# --gradient_checkpointing \
# --show_loss_step 10 \
# --output_dir ./output-glm-freeze


CUDA_VISIBLE_DEVICES=0 deepspeed --master_port 520 train.py \
--train_path /root/autodl-tmp/KB_LLM/data/train_sft.json \
--model_name_or_path /root/autodl-tmp/ptms/THUDM-chatglm-6b/ \
--per_device_train_batch_size 1 \
--max_len 1560 \
--max_src_len 1124 \
--learning_rate 1e-4 \
--weight_decay 0.1 \
--num_train_epochs 10 \
--gradient_accumulation_steps 4 \
--warmup_ratio 0.1 \
--mode glm \
--train_type lora \
--lora_dim 16 \
--lora_alpha 64 \
--lora_dropout 0.1 \
--lora_module_name "query_key_value" \
--seed 1234 \
--ds_file ds_zero2_no_offload.json \
--gradient_checkpointing \
--show_loss_step 10 \
--output_dir ./output-glm-lora