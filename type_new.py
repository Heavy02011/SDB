from sklearn.feature_extraction.text import CountVectorizer as CV
from sklearn.cross_validation import StratifiedKFold
from sklearn.cross_validation import KFold
from sklearn.tree import DecisionTreeClassifier as DT
from sklearn.ensemble import RandomForestClassifier as RFC
from sklearn.ensemble import ExtraTreesClassifier as ETC
from sklearn.ensemble import AdaBoostClassifier as Ada
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import confusion_matrix as CM
from sklearn import tree
from sklearn.preprocessing import normalize
from collections import defaultdict
import numpy as np
import math
import random
import pylab as pl

#input1 = [i.strip().split('\\')[-2]+i.strip().split('\\')[-1][:-4] for i in open('sdh_pt_name').readlines()]
#input1 = [i.strip().split('\\')[-1][:-4] for i in open('sdh_pt_name').readlines()]
#input2 = np.genfromtxt('sdh_45min', delimiter=',')
input1 = [i.strip().split('\\')[-1][:-4] for i in open('rice_pt_name').readlines()]
input2 = np.genfromtxt('rice_45min', delimiter=',')
label1 = input2[:,-1]
#label2 = input4[:,-1]

'''
first do AL using string features to generate labels
and train a data feature model on the generated labels
'''
iteration = 70
fold = 60
#skf = StratifiedKFold(label1, n_folds=fold)
kf = KFold(len(label1), n_folds=fold, shuffle=True)
folds = [[] for i in range(fold)]
i = 0
for train, test in kf:
    folds[i] = test
    i+=1

#clf = ETC(n_estimators=10, criterion='entropy')
clf = RFC(n_estimators=50, criterion='entropy')
#clf = DT(criterion='entropy', random_state=0)
#clf = SVC(kernel='linear')

vc = CV(analyzer='char_wb', ngram_range=(2,4), min_df=1, token_pattern='[a-z]{2,}')
#vc = CV(token_pattern='[a-z]{2,}')
data1 = vc.fit_transform(input1).toarray()
for fd in range(1):
    train = np.hstack((folds[(fd+x)%fold] for x in range(1)))
    validate = np.hstack((folds[(fd+x)%fold] for x in range(1,30)))
    #cut train to one example
    validate = np.append(validate,train[2:])
    train = train[:2]

    test = np.hstack((folds[(fd+x)%fold] for x in range(30,fold)))
    test_data = data1[test]
    test_label = label1[test]

    for itr in range(iteration):
        train_data = data1[train]
        train_label = label1[train]
        validate_data = data1[validate]
        validate_label = label1[validate]

        #for building a data based model to predict another bldg
        clf.fit(train_data, train_label)
        acc = clf.score(test_data, test_label)
        model_label = clf.predict(test_data)

        #entropy based example selection block
        #compute entropy for each instance and rank
        label_pr = np.sort(clf.predict_proba(validate_data)) #sort in ascending order
        preds = clf.predict(validate_data)
        res = []
        for h,i,j,pr in zip(validate,validate_label,preds,label_pr):
            entropy = np.sum(-p*math.log(p,6) for p in pr if p!=0)
            if len(pr)<2:
                margin = 1
            else:
                margin = pr[-1]-pr[-2]
            res.append([h,i,j,entropy,margin])
        #print 'iter', itr, 'wrong #', len(wrong)

        '''
        #Entropy-based, sort and pick the one with largest H
        res = sorted(res, key=lambda x: x[-2], reverse=True)
        idx = 0

        '''
        #Margin-based, sort and pick the one with least margin
        res = sorted(res, key=lambda x: x[-1])
        idx = 0
        '''

        #least confidence based
        tmp = sorted(label_pr, key=lambda x: x[-1])
        idx = 0


        #Expectation-based, pick the one with H most close to 0.5
        for i in res:
            i[-2] = abs(i[-2]-0.5)
        res = sorted(res, key=lambda x: x[3])
        idx = 0


        #randomly pick one
        idx = random.randint(0,len(res)-1)
        '''

        elmt = res[idx][0]
        #print 'running fold %d iter %d'%(fd, itr)
        #print label1[elmt]

        '''
        #minimal future expected error
        loss = []
        label_pr = clf.predict_proba(validate_data)
        clx = clf.classes_
        for i, pr in zip(validate, label_pr):
            #print 'validate ex#', i
            #print 'pr vector', pr
            new_train = np.append(train,i)
            new_validate = validate[validate!=i]

            new_train_data = data1[new_train]
            new_train_label = label1[new_train]
            new_validate_data = data1[new_validate]
            new_validate_label = label1[new_validate]

            err = 0
            for j in range(len(pr)):
                #compute the sum of confidence for the rest of examples in validate set
                #on the new re-trained model after each possbile labeling (x,y_i) of i is added to the train set
                if pr[j]==0:
                    continue

                new_train_label[-1] = clx[j]
                clf.fit(new_train_data, new_train_label)
                confidence_sum = np.sum(1-np.sort(clf.predict_proba(new_validate_data))[:,-1])
                err += pr[j]*confidence_sum

            loss.append([i,err])

        loss = sorted(loss, key=lambda x: x[-1])
        #print loss

        elmt = loss[0][0]
        '''

        #remove the item from validate set
        #add it to train set
        train = np.append(train, elmt)
        validate = validate[validate!=elmt]
        #train_idx.append(elmt)
        #test_idx.remove(elmt)
print 'acc on string prediciton is', acc

'''
second apply the trained data model on another bldg to predict the labels
'''
input1 = np.genfromtxt('rice_45min', delimiter=',')
data1 = input1[:,[0,1,2,3,5,6,7]]
label1 = input1[:,-1]
input2 = np.genfromtxt('sdh_45min', delimiter=',')
data2 = input2[:,[0,1,2,3,5,6,7]]
label2 = input2[:,-1]
train_data = data1[test]
train_label = model_label
test_data = data2
test_label = label2
clf = RFC(n_estimators=50, criterion='entropy')
clf.fit(train_data, train_label)
preds = clf.predict(test_data)
print 'acc by data model', clf.score(test_data, test_label)

#compute 'confidence' for each example in the new bldg
label_pr = np.sort(clf.predict_proba(test_data)) #sort each prob vector in ascending order
cfdn_d = defaultdict(list)
for h,i,pr in zip(range(len(test_data)),preds,label_pr):
    entropy = np.sum(-p*math.log(p,6) for p in pr if p!=0)
    if len(pr)<2:
        margin = 1
    else:
        margin = pr[-1]-pr[-2]
    cfdn_d[h].append([i,entropy,margin])

'''
third, again, run AL on string feature for the new bldg
'''
#input1 = [i.strip().split('\\')[-2]+i.strip().split('\\')[-1][:-4] for i in open('sdh_pt_name').readlines()]
input1 = [i.strip().split('\\')[-1][:-4] for i in open('sdh_pt_name').readlines()]
input2 = np.genfromtxt('sdh_45min', delimiter=',')
label_gt = input2[:,-1]
label1 = preds

iteration = 120
fold = 20
kf = KFold(len(label1), n_folds=fold, shuffle=True)
folds = [[] for i in range(fold)]
i = 0
for train, test in kf:
    folds[i] = test
    i+=1

acc_sum = [[] for i in range(iteration)]
acc_Md = []
clf = RFC(n_estimators=50, criterion='entropy')
#clf = DT(criterion='entropy', random_state=0)
#clf = SVC(kernel='linear')

vc = CV(analyzer='char_wb', ngram_range=(2,4), min_df=1, token_pattern='[a-z]{2,}')
#vc = CV(token_pattern='[a-z]{2,}')
data1 = vc.fit_transform(input1).toarray()
for fd in range(fold):
    print 'running AL on new bldg - fold', fd
    train = np.hstack((folds[(fd+x)%fold] for x in range(1)))
    validate = np.hstack((folds[(fd+x)%fold] for x in range(1,10)))
    #cut train to one example
    validate = np.append(validate,train[2:])
    train = train[:2]

    test = np.hstack((folds[(fd+x)%fold] for x in range(10,fold)))
    test_data = data1[test]
    test_label = label_gt[test]
    acc_Md.append(accuracy_score(test_label, label1[test]))

    for itr in range(iteration):
        train_data = data1[train]
        train_label = label1[train]
        validate_data = data1[validate]
        validate_label = label1[validate]

        clf.fit(train_data, train_label)
        acc = clf.score(test_data, test_label)
        acc_sum[itr].append(acc)

        #entropy based example selection block
        #compute entropy for each instance and rank
        label_pr = np.sort(clf.predict_proba(validate_data)) #sort in ascending order
        preds = clf.predict(validate_data)
        res = []
        for h,i,pr in zip(validate,preds,label_pr):
            entropy = np.sum(-p*math.log(p,6) for p in pr if p!=0)
            if len(pr)<2:
                margin = 1
            else:
                margin = pr[-1]-pr[-2]
            cfdn = cfdn_d[h][0][-1]
            res.append([h,i,entropy,cfdn/(margin+1)])

        res = sorted(res, key=lambda x: x[-1], reverse=True)
        elmt = res[idx][0]
        train = np.append(train, elmt)
        validate = validate[validate!=elmt]

print 'acc from Md', np.mean(acc_Md)
ave_acc = [np.mean(acc) for acc in acc_sum]
acc_std = [np.std(acc) for acc in acc_sum]

print 'overall acc:', repr(ave_acc)
print 'acc std:', repr(acc_std)


preds = clf.predict(test_data)
cm_ = CM(test_label,preds)
cm = normalize(cm_.astype(np.float), axis=1, norm='l1')
fig = pl.figure()
ax = fig.add_subplot(111)
cax = ax.matshow(cm)
fig.colorbar(cax)
for x in xrange(len(cm)):
    for y in xrange(len(cm)):
        ax.annotate(str("%.3f(%d)"%(cm[x][y],cm_[x][y])), xy=(y,x),
                    horizontalalignment='center',
                    verticalalignment='center')
cls = ['co2','humidity','rmt','stpt','flow','other_t']
pl.xticks(range(len(cm)),cls)
pl.yticks(range(len(cm)),cls)
pl.title('Confusion matrix (%.3f)'%clf.score(test_data, test_label))
pl.ylabel('True label')
pl.xlabel('Predicted label')
pl.show()

cm_ = CM(test_label, label1[test])
cm = normalize(cm_.astype(np.float), axis=1, norm='l1')
fig = pl.figure()
ax = fig.add_subplot(111)
cax = ax.matshow(cm)
fig.colorbar(cax)
for x in xrange(len(cm)):
    for y in xrange(len(cm)):
        ax.annotate(str("%.3f(%d)"%(cm[x][y],cm_[x][y])), xy=(y,x),
                    horizontalalignment='center',
                    verticalalignment='center')
cls = ['co2','humidity','rmt','stpt','flow','other_t']
pl.xticks(range(len(cm)),cls)
pl.yticks(range(len(cm)),cls)
pl.title('Confusion matrix (%.3f)'%accuracy_score(test_label, label1[test]))
pl.ylabel('True label')
pl.xlabel('Predicted label')
pl.show()