# ERFNet full model definition for Pytorch
# Sept 2017
# Eduardo Romera
#######################

import torch
import torch.nn as nn
import torch.nn.init as init
import torch.nn.functional as F

class DownsamplerBlock (nn.Module):
    def __init__(self, ninput, noutput):
        super().__init__()

        self.conv = nn.Conv2d(ninput, noutput-ninput, (3, 3), stride=2, padding=1, bias=True)
        self.pool = nn.MaxPool2d(2, stride=2)
        self.bn = nn.BatchNorm2d(noutput, eps=1e-3)

    def forward(self, input):
        output = torch.cat([self.conv(input), self.pool(input)], 1)
        output = self.bn(output)
        return F.relu(output)
    
    #TODO: 1Dv28 downsampler has dropout as well

class non_bottleneck_1d (nn.Module):
    def __init__(self, chann, dropprob, dilated):        #TODO: check if 3x1 is height in Torch 
        super().__init__()

        self.conv3x1_1 = nn.Conv2d(chann, chann, (3, 1), stride=1, padding=(1,0), bias=True)

        self.conv1x3_1 = nn.Conv2d(chann, chann, (1,3), stride=1, padding=(0,1), bias=True)

        self.bn1 = nn.BatchNorm2d(chann, eps=1e-03)

        self.conv3x1_2 = nn.Conv2d(chann, chann, (3, 1), stride=1, padding=(1*dilated,0), bias=True, dilation = (dilated,1))

        self.conv1x3_2 = nn.Conv2d(chann, chann, (1,3), stride=1, padding=(0,1*dilated), bias=True, dilation = (1, dilated))

        self.bn2 = nn.BatchNorm2d(chann, eps=1e-03)

        self.dropout = nn.Dropout2d(dropprob)
        
    def forward(self, input):

        output = self.conv3x1_1(input)
        output = F.relu(output)
        output = self.conv1x3_1(output)
        output = self.bn1(output)
        output = F.relu(output)

        output = self.conv3x1_2(output)
        output = F.relu(output)
        output = self.conv1x3_2(output)
        output = self.bn2(output)
        #output = F.relu(output)    #ESTO ESTABA MAL

        if (self.dropout.p != 0):
            output = self.dropout(output)
        
        return F.relu(output+input)    #+input = identity (residual connection)

class non_bottleneck_1d_hier (nn.Module):
    def __init__(self):
        super().__init__()
    
        self.conv3x1_1 = nn.Conv2d(128, 128, (3, 1), stride=1, padding=(1,0), bias=True)

        self.conv1x3_1 = nn.Conv2d(128, 128, (1,3), stride=1, padding=(0,1), bias=True)

        self.bn1 = nn.BatchNorm2d(128, eps=1e-03)

        self.conv3x1_22 = nn.Conv2d(128, 128, (3, 1), stride=1, padding=(2,0), bias=True, dilation = (2,1))
        self.conv1x3_22 = nn.Conv2d(128, 128, (1,3), stride=1, padding=(0,2), bias=True, dilation = (1, 2))

        self.conv3x1_24 = nn.Conv2d(128, 128, (3, 1), stride=1, padding=(4,0), bias=True, dilation = (4,1))
        self.conv1x3_24 = nn.Conv2d(128, 128, (1,3), stride=1, padding=(0,4), bias=True, dilation = (1, 4))

        self.conv3x1_28 = nn.Conv2d(128, 128, (3, 1), stride=1, padding=(8,0), bias=True, dilation = (8,1))
        self.conv1x3_28 = nn.Conv2d(128, 128, (1,3), stride=1, padding=(0,8), bias=True, dilation = (1, 8))

        self.conv3x1_216 = nn.Conv2d(128, 128, (3, 1), stride=1, padding=(16,0), bias=True, dilation = (16,1))
        self.conv1x3_216 = nn.Conv2d(128, 128, (1,3), stride=1, padding=(0,16), bias=True, dilation = (1, 16))

        self.bn2 = nn.BatchNorm2d(128, eps=1e-03)

        self.dropout = nn.Dropout2d(0.3)

    def forward(self, input):
        output = self.conv3x1_1(input)
        output = F.relu(output)
        output = self.conv1x3_1(output)
        output = self.bn1(output)
        output = F.relu(output)

        output2 = self.conv3x1_22(output)
        output2 = F.relu(output2)
        output2 = self.conv1x3_22(output2)
        output2 = self.bn2(output2)
        if (self.dropout.p != 0):
            output2 = self.dropout(output2)

        output4 = self.conv3x1_24(output)
        output4 = F.relu(output4)
        output4 = self.conv1x3_24(output4)
        output4 = self.bn2(output4)
        if (self.dropout.p != 0):
            output4 = self.dropout(output4)

        output8 = self.conv3x1_28(output)
        output8 = F.relu(output8)
        output8 = self.conv1x3_28(output8)
        output8 = self.bn2(output8)
        if (self.dropout.p != 0):
            output8 = self.dropout(output8)

        output16 = self.conv3x1_216(output)
        output16 = F.relu(output16)
        output16 = self.conv1x3_216(output16)
        output16 = self.bn2(output16)
        if (self.dropout.p != 0):
            output16 = self.dropout(output16)

        return F.relu(output2+output4+output8+output16+input)

class Encoder(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.initial_block = DownsamplerBlock(3,16)

        self.layers = nn.ModuleList()

        self.layers.append(DownsamplerBlock(16,64))

        for x in range(0, 5):    #5 times
           self.layers.append(non_bottleneck_1d(64, 0.03, 1))   #Dropout here was wrong in prev trainings

        self.layers.append(DownsamplerBlock(64,128))

        for x in range(0, 2):    #2 times
            self.layers.append(non_bottleneck_1d_hier())
            #self.layers.append(non_bottleneck_1d(128, 0.3, 2))
            #self.layers.append(non_bottleneck_1d(128, 0.3, 4))
            #self.layers.append(non_bottleneck_1d(128, 0.3, 8))
            #self.layers.append(non_bottleneck_1d(128, 0.3, 16))

        #TODO: descomentar para encoder
        self.output_conv = nn.Conv2d(128, num_classes, 1, stride=1, padding=0, bias=True)

    def forward(self, input, predict=False):
        output = self.initial_block(input)

        for layer in self.layers:
            output = layer(output)

        if predict:
            output = self.output_conv(output)

        return output


class UpsamplerBlock (nn.Module):
    def __init__(self, ninput, noutput):
        super().__init__()
        self.conv = nn.ConvTranspose2d(ninput, noutput, 3, stride=2, padding=1, output_padding=1, bias=True)
        self.bn = nn.BatchNorm2d(noutput, eps=1e-3)

    def forward(self, input):
        output = self.conv(input)
        output = self.bn(output)
        return F.relu(output)

class PSPDec(nn.Module):

    def __init__(self, in_features, out_features, downsize, upsize=(30,40)):
        super(PSPDec,self).__init__()

        self.features = nn.Sequential(
            nn.AvgPool2d(downsize, stride=downsize),
            nn.Conv2d(in_features, out_features, 1, bias=False),
            nn.BatchNorm2d(out_features, momentum=.95),
            nn.ReLU(inplace=True),
            #nn.UpsamplingBilinear2d(upsize)
            nn.Upsample(size=upsize, mode='bilinear')
        )

    def forward(self, x):
        return self.features(x)

class Decoder (nn.Module):
    def __init__(self, num_classes):
        super().__init__()

        #H=480/8 240/8
        #W=640/8 320/8
        self.layer5a = PSPDec(128, 32, (30,40),(30,40))
        self.layer5b = PSPDec(128, 32, (int(15),int(20)),(30,40))
        self.layer5c = PSPDec(128, 32, (int(7.5),int(10)),(30,40))
        self.layer5d = PSPDec(128, 32, (int(3.75),int(5)),(30,40))

        self.final = nn.Sequential(
            nn.Conv2d(256, 256, 3, padding=1, bias=False),
            nn.BatchNorm2d(256, momentum=.95),
            nn.ReLU(inplace=True),
            nn.Dropout(.1),
            nn.Conv2d(256, num_classes, 1),
        )


    def forward(self, x):
        #x=x[0]
        
        x = self.final(torch.cat([
            x,
            self.layer5a(x),
            self.layer5b(x),
            self.layer5c(x),
            self.layer5d(x),
        ], 1))

        #print('final', x.size())

        return F.upsample(x,size=(240,320), mode='bilinear')

#ERFNet
class Net(nn.Module):
    def __init__(self, num_classes, encoder=None):  #use encoder to pass pretrained encoder
        super().__init__()

        if (encoder == None):
            self.encoder = Encoder(num_classes)
        else:
            self.encoder = encoder

        self.decoder = Decoder(num_classes)

    def forward(self, input, only_encode=False):
        if only_encode:
            return self.encoder.forward(input, predict=True)
        else:
            output = self.encoder(input)    #predict=False by default
            return self.decoder.forward(output)
