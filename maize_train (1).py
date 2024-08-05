# -*- coding: utf-8 -*-
"""Maize Train.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1ba96LW9BSe-TmaTRcOHM2lsfJmiA4RY4
"""

import pandas as pd

# Load the datasets
prices_weather_production_df = pd.read_csv('/content/Food_Prices_Kenya.csv')
counties_regions_df = pd.read_csv('/content/Kenyan_Counties_with_Regions.csv')

# Display the first few rows to understand the structure
print(prices_weather_production_df.head())
print(counties_regions_df.head())

# Clean the Food_Prices_Kenya dataset
prices_weather_production_df = prices_weather_production_df.loc[:, ~prices_weather_production_df.columns.str.contains('^Unnamed')]
prices_weather_production_df = prices_weather_production_df.drop(0)
prices_weather_production_df = prices_weather_production_df.dropna()

# Display the cleaned data
print(prices_weather_production_df.head())

# Merge the datasets
merged_df = pd.merge(prices_weather_production_df, counties_regions_df, left_on='Regions', right_on='Region', how='left')
merged_df = merged_df.drop(columns=['Region'])

# Display the merged data
print(merged_df.head())

from sklearn.preprocessing import StandardScaler

# Convert date-related columns to datetime format
merged_df['Date'] = pd.to_datetime(merged_df['Date'], errors='coerce')
merged_df['Year'] = merged_df['Date'].dt.year
merged_df['Month'] = merged_df['Date'].dt.month

# Replace commas in numeric columns and convert to numeric type
for col in ['Price', 'Usdprice', 'Amount Produced', 'Annual Rainfall', 'Annual Temperature']:
    merged_df[col] = merged_df[col].str.replace(',', '', regex=True).astype(float)

# Normalize or scale numeric features
#scaler = StandardScaler()
#merged_df[['Price', 'Usdprice', 'Amount Produced', 'Annual Rainfall', 'Annual Temperature']] = scaler.fit_transform(
    #merged_df[['Price', 'Usdprice', 'Amount Produced', 'Annual Rainfall', 'Annual Temperature']])

# Display the normalized data
print(merged_df.head())

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor

# Define the feature set and target variable for price prediction
X_price = merged_df[['Year', 'Month', 'Amount Produced', 'Annual Rainfall', 'Annual Temperature']]
y_price = merged_df['Price']

# Define the feature set and target variables for weather prediction
X_weather = merged_df[['Year', 'Month']]
y_rainfall = merged_df['Annual Rainfall']
y_temperature = merged_df['Annual Temperature']

# Split the data into training and testing sets
X_train_price, X_test_price, y_train_price, y_test_price = train_test_split(X_price, y_price, test_size=0.2, random_state=42)
X_train_weather, X_test_weather, y_train_rainfall, y_test_rainfall, y_train_temperature, y_test_temperature = train_test_split(
    X_weather, y_rainfall, y_temperature, test_size=0.2, random_state=42)

# Display the shapes of the training and testing sets
print(X_train_price.shape, X_test_price.shape, y_train_price.shape, y_test_price.shape)
print(X_train_weather.shape, X_test_weather.shape, y_train_rainfall.shape, y_test_rainfall.shape, y_train_temperature.shape, y_test_temperature.shape)

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

# ANN model for maize price prediction
def build_price_model():
    model = Sequential()
    model.add(Dense(128, input_dim=X_train_price.shape[1], activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(1))  # Output layer for regression
    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mean_absolute_error'])
    return model

# ANN model for weather prediction
def build_weather_model():
    model = Sequential()
    model.add(Dense(128, input_dim=X_train_weather.shape[1], activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(2))  # Predicting both rainfall and temperature
    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mean_absolute_error'])
    return model

# Build and train the models
price_model = build_price_model()
price_model.fit(X_train_price, y_train_price, epochs=100, batch_size=10, validation_split=0.2)

weather_model = build_weather_model()
weather_model.fit(X_train_weather, [y_train_rainfall, y_train_temperature], epochs=100, batch_size=10, validation_split=0.2)

# Evaluate the models
price_loss, price_mae = price_model.evaluate(X_test_price, y_test_price)
print(f'Price Model - Loss: {price_loss}, MAE: {price_mae}')

weather_loss, weather_mae = weather_model.evaluate(X_test_weather, [y_test_rainfall, y_test_temperature])
print(f'Weather Model - Loss: {weather_loss}, MAE: {weather_mae}')

# Hyperparameter tuning for Random Forest using GridSearchCV
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [None, 10, 20, 30],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}

rf = RandomForestRegressor(random_state=42)
grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, cv=3, n_jobs=-1, verbose=2)
grid_search.fit(X_train_price, y_train_price)
best_params = grid_search.best_params_
print(f"Best parameters: {best_params}")

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
# Train the best Random Forest model
best_rf = RandomForestRegressor(**best_params)
best_rf.fit(X_train_price, y_train_price)
price_predictions = best_rf.predict(X_test_price)

# Display the evaluation results for the Random Forest model
rf_mae = mean_absolute_error(y_test_price, price_predictions)
rf_mse = mean_squared_error(y_test_price, price_predictions)
rf_r2 = r2_score(y_test_price, price_predictions)
print(f"Random Forest - MAE: {rf_mae}, MSE: {rf_mse}, R2: {rf_r2}")