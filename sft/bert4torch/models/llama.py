from bert4torch.models.transformer import Decoder
from bert4torch.snippets import delete_arguments
from bert4torch.layers import BlockIdentity, LlamaFeedForward, NormHead


class LLaMA(Decoder):
    '''LLaMA
    链接: https://github.com/facebookresearch/llama
    1. 去掉bias
    2. rmsnorm
    3. feedForward不同, 三层全连接
    4. rotary相对位置编码
    '''
    @delete_arguments('with_pool', 'with_mlm', 'with_nsp')
    def __init__(self, *args, p_bias='rotary', **kwargs):
        kwargs.update({'p_bias': p_bias, 'weight': True, 'bias': False, 'norm_mode': 'rmsnorm', 
                       'is_decoder': True, 'final_layernorm': True, 'pre_layernorm': True})
        super().__init__(*args, **kwargs)
        del self.embeddings.layerNorm
        self.prefix = 'llama'

        # 修改feedword
        for layer in self.decoderLayer:
            layer.feedForward = LlamaFeedForward(self.hidden_size, **kwargs)
            layer.dropout1 = BlockIdentity()  # llama未使用dropout
            layer.dropout2 = BlockIdentity()
        
        # 修改lm_head，目前在Baichuan2中使用
        if kwargs.get('norm_head') is True:
            self.lm_head = NormHead(self.hidden_size, self.vocab_size)

    def variable_mapping(self):
        # 映射到权重格式
        mapping = super(LLaMA, self).variable_mapping()
        for i in range(self.num_hidden_layers):
            prefix_i = f'{self.prefix}.encoder.layer.%d.' % i
            mapping.update({f'decoderLayer.{i}.feedForward.intermediateDense2.weight': prefix_i + 'intermediate2.dense.weight'})
        return mapping
