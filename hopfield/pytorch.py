import torch
import torch.nn as nn
import torch.nn.functional as F

class MultiLayerPerceptron(nn.Module):
    def __init__(self, input_size, hidden_size1, hidden_size2, num_classes, dropout_rate=0.5):
        """
        多层感知机 (MLP) 构造函数
        
        参数:
        input_size: 输入特征维度
        hidden_size1: 第一个隐藏层神经元数量
        hidden_size2: 第二个隐藏层神经元数量
        num_classes: 输出类别数
        dropout_rate: Dropout比率，默认0.5
        """
        super().__init__()  # 调用父类nn.Module的构造函数
        
        # 定义网络层
        self.fc1 = nn.Linear(input_size, hidden_size1)  # 输入层到第一隐藏层
        self.bn1 = nn.BatchNorm1d(hidden_size1)         # 批归一化层
        
        self.fc2 = nn.Linear(hidden_size1, hidden_size2) # 第一隐藏层到第二隐藏层
        self.bn2 = nn.BatchNorm1d(hidden_size2)         # 批归一化层
        
        self.fc3 = nn.Linear(hidden_size2, num_classes)  # 第二隐藏层到输出层
        
        self.dropout = nn.Dropout(p=dropout_rate)       # Dropout层
        
        # 初始化权重 (He初始化，适合ReLU激活函数)
        self._initialize_weights()
    
    def _initialize_weights(self):
        """初始化网络权重"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
    
    def forward(self, x):
        """
        前向传播
        
        参数:
        x: 输入张量，形状为 [batch_size, input_size]
        
        返回:
        输出张量，形状为 [batch_size, num_classes]
        """
        # 第一层: Linear -> BatchNorm -> ReLU -> Dropout
        x = self.fc1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.dropout(x)
        
        # 第二层: Linear -> BatchNorm -> ReLU -> Dropout
        x = self.fc2(x)
        x = self.bn2(x)
        x = F.relu(x)
        x = self.dropout(x)
        
        # 输出层: Linear (无激活函数，通常与CrossEntropyLoss配合使用)
        x = self.fc3(x)
        
        return x

# 使用示例
if __name__ == "__main__":
    # 超参数
    input_size = 784    # 例如MNIST图像的28x28=784像素
    hidden_size1 = 512  # 第一个隐藏层大小
    hidden_size2 = 256  # 第二个隐藏层大小
    num_classes = 10    # 输出类别数（例如0-9数字分类）
    batch_size = 64
    
    # 实例化模型
    model = MultiLayerPerceptron(input_size, hidden_size1, hidden_size2, num_classes)
    
    # 打印模型结构
    print(model)
    
    # 创建随机输入数据 (模拟一个批次)
    dummy_input = torch.randn(batch_size, input_size)
    
    # 前向传播
    output = model(dummy_input)
    
    print(f"输入形状: {dummy_input.shape}")
    print(f"输出形状: {output.shape}")