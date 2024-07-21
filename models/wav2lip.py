import torch
from torch import nn
from torch.nn import functional as F
import math

from .conv import Conv2dTranspose, Conv2d, nonorm_Conv2d

class Wav2Lip(nn.Module):
    def __init__(self):
        super(Wav2Lip, self).__init__()
        self.face_encoder_blocks = nn.ModuleList([
            nn.Sequential(
                Conv2d(6, 16, kernel_size=7, stride=1, padding=3)),  # 440x440

            nn.Sequential(
                Conv2d(16, 32, kernel_size=5, stride=2, padding=2),
                Conv2d(32, 32, kernel_size=3, stride=1, padding=1, residual=True)),  # 220x220

            nn.Sequential(
                Conv2d(32, 32, kernel_size=3, stride=2, padding=1),
                Conv2d(32, 32, kernel_size=3, stride=1, padding=1, residual=True),
                Conv2d(32, 32, kernel_size=3, stride=1, padding=1, residual=True)),  # 110x110

            nn.Sequential(
                Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
                Conv2d(64, 64, kernel_size=3, stride=1, padding=1, residual=True),
                Conv2d(64, 64, kernel_size=3, stride=1, padding=1, residual=True),
                Conv2d(64, 64, kernel_size=3, stride=1, padding=1, residual=True)),  # 55x55

            nn.Sequential(
                Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
                Conv2d(128, 128, kernel_size=3, stride=1, padding=1, residual=True),
                Conv2d(128, 128, kernel_size=3, stride=1, padding=1, residual=True)),  # 28x28

            nn.Sequential(
                Conv2d(128, 256, kernel_size=3, stride=3, padding=1),
                Conv2d(256, 256, kernel_size=3, stride=1, padding=1, residual=True),
                Conv2d(256, 256, kernel_size=3, stride=1, padding=1, residual=True)),  # 10x10

            nn.Sequential(
                Conv2d(256, 512, kernel_size=3, stride=2, padding=1),
                Conv2d(512, 512, kernel_size=3, stride=1, padding=1, residual=True)),  # 5x5

            nn.Sequential(
                Conv2d(512, 512, kernel_size=3, stride=2, padding=1),
                Conv2d(512, 512, kernel_size=3, stride=1, padding=1, residual=True)),  # 3x3

            nn.Sequential(
                Conv2d(512, 512, kernel_size=1, stride=3, padding=0),
                Conv2d(512, 512, kernel_size=1, stride=1, padding=0)),  # 1x1
        ])
        
        self.audio_encoder = nn.Sequential(
            Conv2d(1, 32, kernel_size=3, stride=1, padding=1),
            Conv2d(32, 32, kernel_size=3, stride=1, padding=1, residual=True),
            Conv2d(32, 32, kernel_size=3, stride=1, padding=1, residual=True),

            Conv2d(32, 64, kernel_size=3, stride=(3, 1), padding=1),
            Conv2d(64, 64, kernel_size=3, stride=1, padding=1, residual=True),
            Conv2d(64, 64, kernel_size=3, stride=1, padding=1, residual=True),

            Conv2d(64, 128, kernel_size=3, stride=3, padding=1),
            Conv2d(128, 128, kernel_size=3, stride=1, padding=1, residual=True),
            Conv2d(128, 128, kernel_size=3, stride=1, padding=1, residual=True),

            Conv2d(128, 256, kernel_size=3, stride=(3, 2), padding=1),
            Conv2d(256, 256, kernel_size=3, stride=1, padding=1, residual=True),

            Conv2d(256, 512, kernel_size=3, stride=1, padding=0),
            Conv2d(512, 512, kernel_size=1, stride=1, padding=0),)

        self.face_decoder_blocks = nn.ModuleList([
            nn.Sequential(
                Conv2d(512, 512, kernel_size=1, stride=1, padding=0)
            ),  # 1,1 -> 1,1
            
            nn.Sequential(
                Conv2dTranspose(1024, 512, kernel_size=3, stride=1, padding=0),  # 1,1 -> 3,3
                Conv2d(512, 512, kernel_size=3, stride=1, padding=1, residual=True)
            ),
            
            nn.Sequential(
                Conv2dTranspose(1024, 512, kernel_size=3, stride=2, padding=1,output_padding=0),  # 3,3 -> 5,5
                Conv2d(512, 512, kernel_size=3, stride=1, padding=1, residual=True),
                Conv2d(512, 512, kernel_size=3, stride=1, padding=1, residual=True)
            ),
            
            nn.Sequential(Conv2dTranspose(1024, 512, kernel_size=3, stride=2, padding=1,output_padding=1),  # 5,5 -> 10,10
                Conv2d(512, 512, kernel_size=3, stride=1, padding=1, residual=True),
                Conv2d(512, 512, kernel_size=3, stride=1, padding=1, residual=True)
            ),

            nn.Sequential(Conv2dTranspose(768, 384, kernel_size=3, stride=3, padding=1,output_padding=0),  #10,10 -> 28,28
                Conv2d(384,384, kernel_size=3, stride=1, padding=1, residual=True),
                Conv2d(384,384, kernel_size=3, stride=1, padding=1, residual=True)
            ),
            nn.Sequential(Conv2dTranspose(512, 256, kernel_size=3, stride=2, padding=1,output_padding=0),  #28,28 -> 55,55
                Conv2d(256,256, kernel_size=3, stride=1, padding=1, residual=True),
                Conv2d(256,256, kernel_size=3, stride=1, padding=1, residual=True)
            ),
            nn.Sequential(Conv2dTranspose(320, 128, kernel_size=3, stride=2, padding=1,output_padding=1),  #55,55 -> 110,110
                Conv2d(128,128, kernel_size=3, stride=1, padding=1, residual=True),
                Conv2d(128,128, kernel_size=3, stride=1, padding=1, residual=True)
            ),
            nn.Sequential(Conv2dTranspose(160, 64, kernel_size=3, stride=2, padding=1,output_padding=1),  #110,110 -> 220,220
                Conv2d(64,64, kernel_size=3, stride=1, padding=1, residual=True),
                Conv2d(64,64, kernel_size=3, stride=1, padding=1, residual=True)
            ),
            nn.Sequential(Conv2dTranspose(96, 64, kernel_size=3, stride=2, padding=1,output_padding=1),  #220,220 -> 440,440
                Conv2d(64, 64, kernel_size=3, stride=1, padding=1, residual=True),
                Conv2d(64, 64, kernel_size=3, stride=1, padding=1, residual=True)
            )
        ])
        self.output_block = nn.Sequential(Conv2d(80, 32, kernel_size=3, stride=1, padding=1),
                                          nn.Conv2d(32, 3, kernel_size=1, stride=1, padding=0),
                                          nn.Sigmoid())

    def forward(self, audio_sequences, face_sequences):
        # audio_sequences = (B, T, 1, 80, 16)
        B = audio_sequences.size(0)
        print("audio_sequences size:",audio_sequences.size())

        input_dim_size = len(face_sequences.size())
        if input_dim_size > 4:
            audio_sequences = torch.cat([audio_sequences[:, i] for i in range(audio_sequences.size(1))], dim=0)
            face_sequences = torch.cat([face_sequences[:, :, i] for i in range(face_sequences.size(2))], dim=0)

        audio_embedding = self.audio_encoder(audio_sequences) # B, 512, 1, 1

        feats = []
        x = face_sequences
        print("face_sequences size:",x.size())
        for f in self.face_encoder_blocks:
            x = f(x)
            print("x=f(x) size for encoder:",x.size())
            feats.append(x)

        x = audio_embedding
        print("audio_embedding size:",x.size())
        print("len feats",len(feats))
        print("feats before loop size:",feats[-1].size())
        
        for f in self.face_decoder_blocks:
            x = f(x)
            print("x=f(x) size for decoder:",x.size())
            try:
                x = torch.cat((x, feats[-1]), dim=1)
            except Exception as e:
                print("x size:",x.size())
                print("feats size:",feats[-1].size())
                raise e
            
            feats.pop()

        x = self.output_block(x)

        if input_dim_size > 4:
            x = torch.split(x, B, dim=0) # [(B, C, H, W)]
            outputs = torch.stack(x, dim=2) # (B, C, T, H, W)

        else:
            outputs = x
            
        return outputs



class Wav2Lip_disc_qual(nn.Module):
    def __init__(self):
        super(Wav2Lip_disc_qual, self).__init__()

        self.face_encoder_blocks = nn.ModuleList([
            nn.Sequential(nonorm_Conv2d(3, 32, kernel_size=7, stride=1, padding=3)), # 220,440

            nn.Sequential(nonorm_Conv2d(32, 64, kernel_size=5, stride=(1, 2), padding=2), # 220, 220
            nonorm_Conv2d(64, 64, kernel_size=5, stride=1, padding=2)),

            nn.Sequential(nonorm_Conv2d(64, 128, kernel_size=5, stride=2, padding=2),    # 110,110
            nonorm_Conv2d(128, 128, kernel_size=5, stride=1, padding=2)),
            
            nn.Sequential(nonorm_Conv2d(128, 128, kernel_size=5, stride=2, padding=2),    # 55,55
            nonorm_Conv2d(128, 128, kernel_size=5, stride=1, padding=2)),

            nn.Sequential(nonorm_Conv2d(128, 256, kernel_size=5, stride=2, padding=2),   # 28,28
            nonorm_Conv2d(256, 256, kernel_size=5, stride=1, padding=2)),
            
            nn.Sequential(nonorm_Conv2d(256, 256, kernel_size=3, stride=3, padding=1),   # 10,10
            nonorm_Conv2d(256, 256, kernel_size=3, stride=1, padding=1)),

            nn.Sequential(nonorm_Conv2d(256, 512, kernel_size=3, stride=2, padding=1),       # 5,5
            nonorm_Conv2d(512, 512, kernel_size=3, stride=1, padding=1)),

            nn.Sequential(nonorm_Conv2d(512, 512, kernel_size=3, stride=2, padding=1),     # 3,3
            nonorm_Conv2d(512, 512, kernel_size=3, stride=1, padding=1),),
            
            nn.Sequential(nonorm_Conv2d(512, 512, kernel_size=3, stride=1, padding=0),     # 1, 1
            nonorm_Conv2d(512, 512, kernel_size=1, stride=1, padding=0)),])
        

        self.binary_pred = nn.Sequential(nn.Conv2d(512, 1, kernel_size=1, stride=1, padding=0), nn.Sigmoid())
        self.label_noise = .0

    def get_lower_half(self, face_sequences):
        return face_sequences[:, :, face_sequences.size(2)//2:]

    def to_2d(self, face_sequences):
        B = face_sequences.size(0)
        face_sequences = torch.cat([face_sequences[:, :, i] for i in range(face_sequences.size(2))], dim=0)
        return face_sequences

    def perceptual_forward(self, false_face_sequences):
        false_face_sequences = self.to_2d(false_face_sequences)
        false_face_sequences = self.get_lower_half(false_face_sequences)

        false_feats = false_face_sequences
        for f in self.face_encoder_blocks:
            false_feats = f(false_feats)

        false_pred_loss = F.binary_cross_entropy(self.binary_pred(false_feats).view(len(false_feats), -1), 
                                        torch.ones((len(false_feats), 1)).cuda())

        return false_pred_loss

    def forward(self, face_sequences):
        face_sequences = self.to_2d(face_sequences)
        face_sequences = self.get_lower_half(face_sequences)

        x = face_sequences

        for f in self.face_encoder_blocks:
            x = f(x)

        return self.binary_pred(x).view(len(x), -1)