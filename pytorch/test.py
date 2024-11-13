import torch
from torch import nn
import matplotlib.pyplot as plt

# Data
X = torch.arange(0, 1, 0.01).unsqueeze(1)
y = 2 * X + 1

# Model
class LinearRegressionModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(in_features=1, out_features=1)
    
    def forward(self, x):
        return self.linear(x)

model = LinearRegressionModel()

# Loss and optimizer
loss_fn = nn.MSELoss()
optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

# Training
epochs = 1000
for epoch in range(epochs):
    model.train()
    y_pred = model(X)
    loss = loss_fn(y_pred, y)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    if epoch % 100 == 0:
        print(f"Epoch {epoch}: Loss = {loss.item()}")

# Inference
model.eval()
with torch.no_grad():
    y_pred = model(X)

# Plotting
plt.scatter(X, y, label="True Data")
plt.plot(X, y_pred, color="red", label="Predictions")
plt.legend()
plt.show()

# Saving and loading the model
torch.save(model.state_dict(), "linear_regression_model.pth")
loaded_model = LinearRegressionModel()
loaded_model.load_state_dict(torch.load("linear_regression_model.pth"))
loaded_model.eval()

