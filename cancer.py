#!/usr/bin/python3
import cgi
import numpy as np
import pandas as pd
from sklearn import datasets
from sklearn import linear_model
from sklearn import cross_validation
from pandas import DataFrame
cancer = datasets.load_breast_cancer()
df = pd.DataFrame(np.c_[cancer['data'], cancer['target']],
                  columns=np.append(cancer['feature_names'], ['target']))
form = cgi.FieldStorage()
mean_perimeter = form.getvalue('mean_perimeter')
mean_radius = form.getvalue('mean_radius')
rak_list = [[mean_perimeter, mean_radius]]
cancer_from_site = DataFrame(rak_list)
cancer_from_site.columns = ['mean perimeter', 'mean radius']
cancer_frame = DataFrame(cancer.data)
cancer_frame.columns = cancer.feature_names
cancer_frame['target'] = cancer.target
cancer_frame['name'] = cancer_frame.target.apply(lambda x: cancer.target_names[x])
train_data, test_data, train_labels, test_labels = cross_validation.train_test_split(cancer_frame[['mean perimeter',
                                                                                                   'mean radius']],
                                                                                     cancer_frame['target'],
                                                                                     test_size=0)
model = linear_model.SGDClassifier(alpha=1e-05, n_iter=989, random_state=0)
scores = cross_validation.cross_val_score(model, train_data, train_labels, cv=10)
test_data = cancer_from_site
model.fit(train_data, train_labels)
model_predictions = model.predict(test_data)
print(model_predictions)
