#%% Cargando librerias #
import pandas as pd
import numpy as np

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

from sklearn.preprocessing import OneHotEncoder, LabelEncoder, MinMaxScaler, OrdinalEncoder

from imblearn.over_sampling import RandomOverSampler, SMOTE
from imblearn.under_sampling import RandomUnderSampler

from sklearn.model_selection import train_test_split, GridSearchCV

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, make_scorer


from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from xgboost import XGBClassifier

import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer

import os
import random

from sklearn.base import BaseEstimator, TransformerMixin
import joblib


def softM(num1,LAMBDA=2):
    PI = np.pi
    AVG = np.mean(num1)
    SD = np.std(num1)
    #LAMBDA = 2
    x1 = num1
    vt = (x1- AVG)/(LAMBDA * (SD/(2 * PI)))
    trans = 1/(1 + np.exp(-vt))
    return(trans)

class softMax(BaseEstimator, TransformerMixin):
    def __init__(self,LAMBDA=2):
        self.LAMBDA = LAMBDA
        #self.parametro2 = parametro2
        pass

    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        res = X.apply(softM,LAMBDA=self.LAMBDA)
        return res
    
###########################################






path = "heart_disease_uci.csv"

df = pd.read_csv(path)
df

df["target"] = np.where(df["num"] == 0, "0",
                     np.where(df["num"] > 0, "1", None))

df.describe(include="all")


df.ca


df.isna().apply(np.mean, axis=0).plot(kind='bar')
plt.show()

import joblib
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer, IterativeImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor

# 1. Definición de variables
cat_var = ["sex", "cp", "fbs", "restecg", "exang", "slope", "thal"]
num_var = ["age", "trestbps", "chol", "oldpeak", "ca"]

# 2. Pipelines individuales
# Usamos StandardScaler en lugar de un hipotético softMax
num_pipeline = Pipeline(steps=[
    ("imputer", IterativeImputer(
        estimator=RandomForestRegressor(n_estimators=10, random_state=42),
        random_state=42
    )),
    ("scaler", StandardScaler()) 
])

cat_pipeline = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
])

# 3. Transformador global (Combinamos todo aquí UNA SOLA VEZ)
full_transform = ColumnTransformer(transformers=[
    ("num", num_pipeline, num_var),
    ("cat", cat_pipeline, cat_var)
])

# 4. Ajuste y transformación
X_processed = full_transform.fit_transform(df)

# 5. Guardado y carga
joblib.dump(full_transform, 'transformador.pkl')
transformador = joblib.load('transformador.pkl')

# 6. Uso del transformador cargado (Nota la 's' en transform)
data_transformed = transformador.transform(df)
X = data_transformed 
df["target"].value_counts().plot.bar()
plt.show()


y = df["target"].astype(int)


X_train, X_test, y_train, y_test = train_test_split(X, y, 
                                                    test_size = 0.2, 
                                                    random_state = 1442)

model = XGBClassifier(random_state=153468)
# Definición del rango de valores de los parámetros del modelo
params = { 'max_depth': [4,6,8],#Numero de nodos
           'learning_rate': [0.01, 0.03, 0.05],# eta
           'n_estimators': [100, 200],
           'colsample_bytree': [0.3, 0.7]}
          
grid = GridSearchCV(estimator=model,param_grid=params,refit=True,verbose=3,cv=5,n_jobs=-1)
grid.fit(X_train,y_train)

grid.best_score_
grid.best_params_
joblib.dump(grid, 'model_xgb.pkl')

model = joblib.load('model_xgb.pkl')

y_pred = grid.predict(X_test)
print(confusion_matrix(y_true = y_test, y_pred = y_pred))
print(classification_report(y_true = y_test, y_pred = y_pred))#Output

