import os

import torch
import torch.nn as nn
import torch.optim as optim

current_folder = os.path.dirname(os.path.realpath(__file__))
DEFAULT_MODEL_PATH = current_folder
DEFAULT_MODEL_NAME = "transformer_model.pth"


class TransformerModel(nn.Module):
    def __init__(
        self,
        input_dim,
        num_classes,
        d_model=128,
        nhead=8,
        num_encoder_layers=3,
        dim_feedforward=512,
        dropout=0.1,
    ):
        super().__init__()
        self.embedding = nn.Linear(input_dim, d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model, nhead, dim_feedforward, dropout
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer, num_encoder_layers
        )
        self.fc = nn.Linear(d_model, num_classes)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        x = self.embedding(x)
        x = x.unsqueeze(1)  # Add a dummy sequence length dimension
        x = x.permute(
            1, 0, 2
        )  # Transformer expects input shape: (seq_len, batch_size, d_model)
        x = self.transformer_encoder(x)
        x = x.mean(dim=0)  # Average pooling over sequence length
        x = self.fc(x)
        return self.softmax(x)


class TransformerTaskAssignment:
    def __init__(self, config: dict):
        self.config = config
        self.input_dim = config["input_dim"]
        self.num_classes = config["num_classes"]
        if "d_model" in config:
            self.d_model = config["d_model"]
        else:
            self.d_model = 128
        if "nhead" in config:
            self.nhead = config["nhead"]
        else:
            self.nhead = 8
        if "num_encoder_layers" in config:
            self.num_encoder_layers = config["num_encoder_layers"]
        else:
            self.num_encoder_layers = 3
        if "dim_feedforward" in config:
            self.dim_feedforward = config["dim_feedforward"]
        else:
            self.dim_feedforward = 512
        if "dropout" in config:
            self.dropout = config["dropout"]
        else:
            self.dropout = 0.1
        if "model_path" in config:
            self.model_path = config["model_path"]
        else:
            self.model_path = os.path.join(DEFAULT_MODEL_PATH, "models/")
            if not os.path.exists(self.model_path):
                os.makedirs(self.model_path)
        if "model_name" in config:
            self.model_name = config["model_name"]
        else:
            self.model_name = DEFAULT_MODEL_NAME
        print(f"Model path: {self.model_path}")
        print(f"Model name: {self.model_name}")
        self.save_path = os.path.join(self.model_path, self.model_name)
        print(f"Save path: {self.save_path}")
        self.model = TransformerModel(
            self.input_dim,
            self.num_classes,
            self.d_model,
            self.nhead,
            self.num_encoder_layers,
            self.dim_feedforward,
            self.dropout,
        )
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.CrossEntropyLoss()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def train(self, dataloader, epochs=10):
        self.model.train()
        for epoch in range(epochs):
            for _i, (inputs, labels) in enumerate(dataloader):
                inputs, labels = inputs.to(self.device), labels.to(self.device)
                self.optimizer.zero_grad()
                outputs = self.model(inputs)
                loss = self.criterion(outputs, labels)
                loss.backward()
                self.optimizer.step()
            print(f"Epoch: {epoch + 1}, Loss: {loss.item()}")

    def save_model(self, path=None):
        if path is None:
            path = self.save_path
        torch.save(self.model.state_dict(), path)

    def load_model(self, path=None):
        if path is None:
            path = self.save_path
        print(f"Loading model from {path}")
        self.model.load_state_dict(torch.load(path))
        self.model.eval()

    def predict(self, inputs):
        self.model.eval()
        with torch.no_grad():
            inputs = torch.tensor(inputs).float().to(self.device)
            outputs = self.model(inputs)
            _, predicted = torch.max(outputs, 1)
            return predicted
