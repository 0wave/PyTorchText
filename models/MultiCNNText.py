from .BasicModule import BasicModule
import torch as t
import numpy as np
from torch import nn

class MultiCNNText(BasicModule): 
    def __init__(self, opt ):
        super(MultiCNNText, self).__init__()
        self.model_name = 'MultiCNNText'
        self.opt=opt
        self.encoder = nn.Embedding(opt.vocab_size,opt.embedding_dim)

        title_convs = [ nn.Sequential(
                                nn.Conv1d(in_channels = opt.embedding_dim,
                                        out_channels = opt.title_dim,
                                        kernel_size = kernel_size),
                                nn.ReLU(),
                                nn.MaxPool1d(kernel_size = (opt.title_seq_len - kernel_size + 1))
                            )
         for kernel_size in [3,4,5,6]]

        content_convs = [ nn.Sequential(
                                nn.Conv1d(in_channels = opt.embedding_dim,
                                        out_channels = opt.content_dim,
                                        kernel_size = kernel_size),
                                nn.ReLU(),
                                nn.MaxPool1d(kernel_size = (opt.content_seq_len - kernel_size + 1))
                            )
            for kernel_size in [3,4,5,6]
        ]
        self.title_convs = nn.ModuleList(title_convs)
        self.content_convs = nn.ModuleList(content_convs)

        self.fc = nn.Linear((opt.title_dim+opt.content_dim)*4, opt.num_classes)
        self.drop = nn.Dropout(0.5)

        if opt.embedding_path:
            self.encoder.weight.data.copy_(t.from_numpy(np.load(opt.embedding_path)['vector']))

    def forward(self, title, content):
        title = self.encoder(title)
        content = self.encoder(content)
        title_out = [ title_conv(title.permute(0, 2, 1)) for title_conv in self.title_convs]
        content_out = [ content_conv(content.permute(0,2,1)) for content_conv in self.content_convs]
        conv_out = t.cat((title_out+content_out),dim=1)
        reshaped = conv_out.view(conv_out.size(0), -1)
        logits = self.fc(self.drop(reshaped))
        return logits

    # def get_optimizer(self):  
    #    return  t.optim.Adam([
    #             {'params': self.title_conv.parameters()},
    #             {'params': self.content_conv.parameters()},
    #             {'params': self.fc.parameters()},
    #             {'params': self.encoder.parameters(), 'lr': 5e-4}
    #         ], lr=self.opt.lr)
    # # end method forward


 
if __name__ == '__main__':
    from ..config import opt
    opt.content_dim = 128
    opt.title_dim = 100
    m = MultiCNNText(opt)
    title = t.autograd.Variable(t.arange(0,500).view(10,50)).long()
    content = t.autograd.Variable(t.arange(0,2500).view(10,250)).long()
    o = m(title,content)
    print(o.size())
