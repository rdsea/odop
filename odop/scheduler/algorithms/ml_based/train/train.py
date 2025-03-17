import os
import sys

sys.path.append(os.path.abspath(os.path.join("..")))
import torch
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, TensorDataset
from transformer_algorithm import TransformerTaskAssignment

# Parameters
num_samples = 10000
input_dim = (
    1 + 2 * 100
)  # 1 for time requirement, 2*100 for mem_sub and cpu_sub over 100 seconds
num_classes = 2
batch_size = 32


# Generate random data
time_requirement = torch.randint(
    1, 2000, (num_samples, 1)
)  # Time requirement in seconds
mem_available = (
    torch.rand(num_samples, 100) * 10
)  # Available memory in GB over 100 seconds
mem_requirement = torch.rand(num_samples, 1) * 10  # Memory requirement in GB
cpu_available = torch.randint(
    0, 129, (num_samples, 100)
)  # CPUs available over 100 seconds
cpu_requirement = torch.randint(1, 129, (num_samples, 1))  # CPUs requirement [1-128]

# Calculate mem_sub and cpu_sub
mem_sub = mem_available - mem_requirement
cpu_sub = cpu_available - cpu_requirement

# Concatenate to form the input data
X = torch.cat((time_requirement, mem_sub, cpu_sub), dim=1)
print(X.shape)

# Create labels
labels = (
    (time_requirement < 1000)
    & (mem_sub.min(dim=1, keepdim=True)[0] > 0)
    & (cpu_sub.gt(0).sum(dim=1, keepdim=True) > 80)
)
y = labels.long().squeeze()

# Ensure around 30% true labels (as 1)
while y.sum().item() < 0.3 * num_samples:
    idx = torch.randint(0, num_samples, (1,))
    time_requirement[idx] = torch.randint(1, 1000, (1,))
    mem_requirement[idx] = mem_available[idx].min().unsqueeze(0)
    cpu_requirement[idx] = (cpu_available[idx].sum(dim=1).min() // 2).unsqueeze(0)

    mem_sub[idx] = mem_available[idx] - mem_requirement[idx]
    cpu_sub[idx] = cpu_available[idx] - cpu_requirement[idx]
    X[idx] = torch.cat((time_requirement[idx], mem_sub[idx], cpu_sub[idx]), dim=1)
    y[idx] = 1

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y)

# Create DataLoader for training and testing sets
train_dataset = TensorDataset(X_train, y_train)
test_dataset = TensorDataset(X_test, y_test)

train_dataloader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_dataloader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

config_dict = {
    "input_dim": input_dim,
    "num_classes": num_classes,
    "d_model": 128,
    "nhead": 8,
    "num_encoder_layers": 3,
    "dim_feedforward": 512,
    "dropout": 0.1,
    "learning_rate": 0.001,
    "num_epochs": 100,
    "batch_size": 32,
}

# Initialize the algorithm
algorithm = TransformerTaskAssignment(config_dict)

# train the algorithm
algorithm.train(train_dataloader, epochs=config_dict["num_epochs"])
