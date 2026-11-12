"""NEW Oct 2026 synthetic proof-of-concept. Does not reproduce Figure 4.6.
Run: python3 -m pip install scikit-learn numpy; python3 experiment.py
Uses only synthetic, simulator-assigned labels. No real fraud labels.
"""
import csv, random, pathlib
from collections import defaultdict
from statistics import mean
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix

ROOT=pathlib.Path(__file__).parent
rng=random.Random(20261021)
rows=[]
# 100 independent synthetic auctions, with controlled bidder behavior and labels.
for auction in range(100):
    label = int(auction % 2 == 1) # simulator scenario label, NOT confirmed real fraud
    count=rng.randint(6,10) if not label else rng.randint(12,19)
    gaps=[rng.randint(30,240) if not label else rng.randint(3,40) for _ in range(count-1)]
    increments=[rng.randint(100,1100) if not label else rng.randint(50,200) for _ in range(count-1)]
    alternations=rng.randint(0,1) if not label else rng.randint(3,6)
    # Noise deliberately overlaps normal/suspicious synthetic scenarios.
    if rng.random()<0.2:
        count=rng.randint(9,13)
    features=[count,round(mean(gaps),2),round(mean(increments),2),alternations]
    rows.append([f'SIM-{auction:03d}',*features,label,'SYNTHETIC_SIMULATOR_LABEL'])
headers=['Auction ID','Bid count','Mean interbid seconds','Mean price increment AUD','Alternation count','Scenario label','Label origin']
with (ROOT/'synthetic_cases.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(headers);w.writerows(rows)
train=[r for i,r in enumerate(rows) if i%5!=0]
test=[r for i,r in enumerate(rows) if i%5==0]
X_train=[r[1:5] for r in train]; y_train=[r[5] for r in train]
X_test=[r[1:5] for r in test]; y_test=[r[5] for r in test]

def rules(x):
    count,gap,inc,altern=x
    return int(sum([count>=12,gap<55,inc<=220,altern>=3])>=2)

pred_rule=[rules(x) for x in X_test]
# Unsupervised anomaly model uses ONLY simulator-defined normal train cases.
normal=[x for x,y in zip(X_train,y_train) if y==0]
iso=IsolationForest(random_state=20261021,contamination=.15,n_estimators=100).fit(normal)
pred_iso=[int(v==-1) for v in iso.predict(X_test)]
rf=RandomForestClassifier(n_estimators=100,random_state=20261021,min_samples_leaf=2).fit(X_train,y_train)
pred_rf=rf.predict(X_test).tolist()
report=[]
for name,preds in [('Predefined rule baseline',pred_rule),('Isolation Forest',pred_iso),('Random Forest',pred_rf)]:
    precision,recall,f1,_=precision_recall_fscore_support(y_test,preds,average='binary',zero_division=0)
    tn,fp,fn,tp=confusion_matrix(y_test,preds,labels=[0,1]).ravel()
    report.append([name,round(float(precision),3),round(float(recall),3),round(float(f1),3),int(tp),int(fp),int(fn),int(tn)])
with (ROOT/'synthetic_comparison_results.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['Method','Precision','Recall','F1','TP','FP','FN','TN']);w.writerows(report)
with (ROOT/'test_predictions.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['Synthetic Auction ID','Simulator label','Rule prediction','Isolation Forest prediction','Random Forest prediction']);
    for row,a,b,c in zip(test,pred_rule,pred_iso,pred_rf):w.writerow([row[0],row[5],a,b,c])
print('NEW SYNTHETIC EXPERIMENT (2026) -- NOT 2025 FIGURE 4.6')
print('Seed=20261021; 100 simulated auctions, 80 train/20 test (auction held out).')
for r in report:print('%-26s P=%0.3f R=%0.3f F1=%0.3f TP=%d FP=%d FN=%d TN=%d'%tuple(r))
print('Outputs: synthetic_cases.csv, synthetic_comparison_results.csv, test_predictions.csv')
