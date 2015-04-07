import numpy as np
import matplotlib.pyplot as plt
import math
import random
import re
import itertools
import pylab as pl
from scikits.statsmodels.tools.tools import ECDF
from scipy import stats
from scipy.optimize import curve_fit
from time import time
from collections import defaultdict as dd
from collections import Counter as ct

from sklearn import metrics
from sklearn.cluster import KMeans
from sklearn.cluster import AgglomerativeClustering as AC
from sklearn.mixture import GMM
from sklearn.mixture import DPGMM
from sklearn.preprocessing import StandardScaler
from sklearn.utils import shuffle

from sklearn.feature_extraction.text import CountVectorizer as CV
from sklearn.feature_extraction.text import TfidfVectorizer as TV
from sklearn.cross_validation import StratifiedKFold
from sklearn.cross_validation import KFold
from sklearn.tree import DecisionTreeClassifier as DT
from sklearn.ensemble import RandomForestClassifier as RFC
from sklearn.svm import SVC
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from sklearn.metrics import confusion_matrix as CM
from sklearn import tree
from sklearn.preprocessing import normalize

input1 = [i.strip().split('+')[-1][:-5] for i in open('sdh_pt_new_forrice').readlines()]
input2 = np.genfromtxt('sdh_45min_forrice', delimiter=',')
input3 = [i.strip().split('\\')[-1][:-5] for i in open('rice_pt_forsdh').readlines()]
input4 = np.genfromtxt('rice_45min_forsdh', delimiter=',')
input5 = [i.strip().split('_')[-1][:-5] for i in open('soda_pt_new').readlines()]
input6 = np.genfromtxt('soda_45min_new', delimiter=',')
label1 = input2[:,-1]
label = input4[:,-1]
label1 = input6[:,-1]
#input3 = input5 #quick run of the code using other building
#input3, label = shuffle(input3, label)
name = []
for i in input3:
    s = re.findall('(?i)[a-z]{2,}',i)
    name.append(' '.join(s))

cv = CV(analyzer='char_wb', ngram_range=(3,4))
#tv = TV(analyzer='char_wb', ngram_range=(3,4))
fn = cv.fit_transform(name).toarray()
#fn = cv.fit_transform(input1).toarray()
fd = input4[:,[0,1,2,3,5,6,7]]
print 'class count of true labels of all ex:\n', ct(label)
#n_class = len(np.unique(label))
#print n_class
#print np.unique(label)
#print 'class count from groud truth labels:\n',ct(label)
#kmer = cv.get_feature_names()
#idf = zip(kmer, cv._tfidf.idf_)
#idf = sorted(idf, key=lambda x: x[-1], reverse=True)
#print idf[:20]
#print idf[-20:]
#print cv.get_feature_names()

fold = 10
rounds = 100
clf = LinearSVC()
#clf = SVC(kernel='linear')
#clf = RFC(n_estimators=100, criterion='entropy')

clf.fit(fn, label)
coef = abs(clf.coef_)
weight = np.max(coef, axis=0)
#weight = np.mean(coef,axis=0)
feature_rank = []
for i,j in zip(weight, xrange(len(weight))):
    feature_rank.append([i,j])
feature_rank = sorted(feature_rank,key=lambda x: x[0],reverse=True)
feature_idx=[]
for i in feature_rank:
    if i[0]>=0.05:
        feature_idx.append(i[1])
#print 'feature num', len(feature_idx)
fn = fn[:, feature_idx]

'''
p_same = []
p_diff = []
p_all = []#all pairs
intra_same = []
intra_diff = []
intra_all = []#only intra cluster pairs
inter_same = []
inter_diff = []
inter_all = []#only inter cluster pairs
c = KMeans(init='k-means++', n_clusters=32, n_init=10)
c.fit(fn)
for i in xrange(len(fn)):
    for j in xrange(0,i):
        d = np.linalg.norm(fn[i]-fn[j])
        p_all.append(d)
        if c_labels[i] == c_labels[j]:
            intra_all.append(d)
            if label[i] == label[j]:
            #if label[p[0]] == label[p[1]]:
                intra_same.append(d)
                p_same.append(d)
            else:
                intra_diff.append(d)
                p_diff.append(d)
        else:
            inter_all.append(d)
            if label[i] == label[j]:
                inter_same.append(d)
                p_same.append(d)
            else:
                inter_diff.append(d)
                p_diff.append(d)
print 'true tao', min(p_diff)
'''

#kf = StratifiedKFold(label, n_folds=fold, shuffle=True)
kf = KFold(len(label), n_folds=fold, shuffle=True)
mapping = {1:'co2',2:'humidity',4:'rmt',5:'status',6:'stpt',7:'flow',8:'HW sup',9:'HW ret',10:'CW sup',11:'CW ret',12:'SAT',13:'RAT',17:'MAT',18:'C enter',19:'C leave',21:'occu'}
#X = StandardScaler().fit_transform(fn)
p_acc = [] #pseudo label acc
acc_sum = [[] for i in xrange(rounds)]
acc_ave = dd(list)
tao = 0
alpha_ = 1
for train, test in kf:
    #print 'class count of true labels on cluster training ex:\n', ct(label[train])
    train_fd = fn[train]
    #n_class = len(np.unique(label[train]))
    #c = KMeans(init='k-means++', n_clusters=32, n_init=10)
    c = DPGMM(n_components=50, covariance_type='spherical', alpha=10)
    c.fit(train_fd)
    c_labels = c.predict(train_fd)
    print '# of GMM', len(np.unique(c_labels))
    #dist = np.sort(c.transform(train_fd))
    mu = c.means_
    cov = c._get_covars()
    c_inv = []
    for co in cov:
        c_inv.append(np.linalg.inv(co))
    e_pr = np.sort(c.predict_proba(train_fd))
    ex = dd(list) #example id, distance to centroid
    ex_id = dd(list) #example id for each C
    for i,j,k in zip(c_labels, train, e_pr):
        ex[i].append([j,k[-1]])
        ex_id[i].append(int(j))
    for i,j in ex.items():
        ex[i] = sorted(j, key=lambda x: x[-1], reverse=True)
    km_idx = []
    p_idx = []
    p_label = []
    p_dist = dd()
    #print 'initial exs from k clusters centroid=============================='
    for k,v in ex.items():
        for i in range(1):
            if len(v)<=i:
                continue
            idx = v[i][0]
            km_idx.append(idx)
            #print k,label[idx],input3[idx]
    '''
    #compute all pair dist distribution, set tao to min_X
    fit_dist = []
    fit_same = []
    fit_diff = []
    pair = list(itertools.combinations(km_idx,2))
    for p in pair:
        d = np.linalg.norm(fn[p[0]]-fn[p[1]])
        fit_dist.append(d)
        if label[p[0]] == label[p[1]]:
            fit_same.append(d)
        else:
            fit_diff.append(d)
    src = fit_dist
    src = fit_diff #set tao be the min(inter-class pair dist)/2
    #ecdf = ECDF(src)
    #xdata = np.linspace(min(src), max(src), int((max(src)-min(src))/0.01))
    #ydata = ecdf(xdata)
    tao = alpha*min(src)
    #tao = alpha*min(src)/2
    print 'inital tao', tao
    '''
    '''
    #popt, pcov = curve_fit(sigmoid, xdata, ydata)
    #print popt
    #x_p = np.linspace(min(src), max(src), 100)
    #y_p = sigmoid(x_p, popt[0],popt[1])
    plt.plot(x, y, 'r', label='all_true')
    #plt.plot(x_p, y_p, 'k--', label='fit')
    plt.plot(xdata, ydata, 'k', label='all_prx')
    src = fit_same
    ecdf = ECDF(src)
    xdata = np.linspace(min(src), max(src), int((max(src)-min(src))/0.01))
    ydata = ecdf(xdata)
    plt.plot(xdata, ydata, 'r--', label='same_prx')
    src = fit_diff
    ecdf = ECDF(src)
    xdata = np.linspace(min(src), max(src), int((max(src)-min(src))/0.01))
    ydata = ecdf(xdata)
    plt.plot(xdata, ydata, 'k--', label='diff_prx')
    plt.legend(loc='lower right')
    plt.grid(axis='y')
    plt.show()
    '''
    tao = 1.96
    #with tao, excluding the exs near initial C centroid
    for k,idx in zip(ex.keys(),km_idx):
        tmp = []
        for e in ex_id[k]:
            if e == idx:
                continue
            #d = np.linalg.norm(fn[e]-fn[idx])
            a = fn[e] - mu[k]
            b = c_inv[k]
            d = np.abs(np.dot(np.dot(a,b),a.T))
            if d<tao:
                #p_dist[e] = d
                p_idx.append(e)
                p_label.append(label[idx])
                #if label[idx]!=label[e]:
                #print input3[e],label[idx], label[e],d
            else:
                tmp.append(e)
        if not tmp:
            ex_id.pop(k)
        else:
            ex_id[k] = tmp

    '''
    #find neighbors for each ex within each cluster
    neighbor = dd(list)
    for v in ex.values():
        idx = [vv[0] for vv in v]
        pair = list(itertools.combinations(idx,2))
        for p in pair:
            d = np.linalg.norm(fn[p[0]]-fn[p[1]])
            if d>=6:
                neighbor[p[0]].append([p[1],d])
                neighbor[p[1]].append([p[0],d])
    for k,v in neighbor.items():
        neighbor[k] = sorted(v, key=lambda x: x[-1])
    '''

    cl_id = []
    ex_al = [] #the ex added in each itr
    test_fn = fn[test]
    test_label = label[test]
    for rr in range(rounds):
        if not p_idx:
            train_fn = fn[km_idx]
            train_label = label[km_idx]
        else:
            train_fn = fn[np.hstack((km_idx, p_idx))]
            train_label = np.hstack((label[km_idx], p_label))
        #print 'ct on traing label', ct(train_label)
        clf.fit(train_fn, train_label)
        preds_fn = clf.predict(test_fn)
        #print clf.decision_function(test_fn)
        sub_pred = dd(list) #Mn predicted labels for each cluster
        for k,v in ex_id.items():
            sub_pred[k] = clf.predict(fn[v]) #predict labels for cluster learning set
        acc = accuracy_score(test_label, preds_fn)
        #acc_ = accuracy_score(label[train_], preds_c)
        #print 'acc on test set', acc
        #print 'acc on cluster set', acc_
        acc_sum[rr].append(acc)
        #print 'iteration', rr, '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'
        '''
        for k in ex.keys():
            prev = ex_cur[k]
            nb = neighbor[prev]
            for n in nb:
                if n[0] not in km_idx:
                    km_idx.append(n[0])
                    ex_cur[k] = n[0]
                    ex_al.append([rr,k,label[n[0]],input3[n[0]]])
                    break
        '''

        #the original H based cluster selection
        rank = []
        for k,v in sub_pred.items():
            count = ct(v).values()
            count[:] = [i/float(max(count)) for i in count]
            H = np.sum(-p*math.log(p,2) for p in count if p!=0)
            #H /= len(v)/float(len(train))
            rank.append([k,len(v),H])
            #if rr+1 == 3*n_class:
            #print k,'---',len(v), H
        rank = sorted(rank, key=lambda x: x[-1], reverse=True)
        if not rank:
            break
        idx = rank[0][0] #pick the id of the 1st cluster on the rank
        cl_id.append(idx) #track cluster id on each iteration

        '''
        #for debug
        ss = raw_input('')
        while ss!='+':
            l = debug[int(ss)]
            for ll in l:
                print '<<', ss, ll
            ss = raw_input('')

        l = debug[idx]
        for ll in l:
            print '<<', idx, ll
        '''

        #for cc,ll in sub_pred.items(): #if commented out, the following out also
            #print 'cluster',cc,'# of ex.', len(ll),'# predicted L', len(np.unique(ll))
        cc = idx #id of the cluster picked by H
        c_id = ex_id[cc] #example id of the cluster picked
        sub_label = sub_pred[idx]#used when choosing cluster by H
        #sub_label = ll
        sub_fn = fn[c_id]

        #sub-clustering the cluster
        #c_ = KMeans(init='k-means++', n_clusters=len(np.unique(sub_label)), n_init=10)
        c_ = DPGMM(n_components=len(c_id), covariance_type='spherical', alpha=10)
        c_.fit(sub_fn)
        cc_labels = c_.predict(sub_fn)
        #print '# of sub-GMM', len(np.unique(cc_labels))
        #dist = np.sort(c_.transform(sub_fn))
        mu = c_.means_
        cov = c_._get_covars()
        c_inv = []
        for co in cov:
            c_inv.append(np.linalg.inv(co))
        e_pr = np.sort(c.predict_proba(sub_fn))
        ex_ = dd(list)
        for i,j,k,l in zip(cc_labels, c_id, e_pr, sub_label):
            ex_[i].append([j,l,k[-1]])
        for i,j in ex_.items(): #sort by ex. dist to the centroid for each C
            ex_[i] = sorted(j, key=lambda x: x[-1], reverse=True)
        for k,v in ex_.items():
            if v[0][0] not in km_idx:
                idx = v[0][0]
                km_idx.append(idx)

                '''
                #update tao then remove ex<tao
                fit_dist = []
                fit_same = []
                fit_diff = []
                pair = list(itertools.combinations(km_idx,2))
                for p in pair:
                    d = np.linalg.norm(fn[p[0]]-fn[p[1]])
                    fit_dist.append(d)
                    if label[p[0]] == label[p[1]]:
                        fit_same.append(d)
                    else:
                        fit_diff.append(d)
                src = fit_dist
                src = fit_diff #set tao be the min(inter-class pair dist)/2
                #ecdf = ECDF(src)
                #xdata = np.linspace(min(src), max(src), int((max(src)-min(src))/0.01))
                #ydata = ecdf(xdata)
                tao = alpha_*min(src)
                #tao = alpha_*min(src)/2
                #print '# labeled', len(km_idx)

                tmp = []
                #re-visit exs removed on previous itr with the new tao
                idx_tmp=[]
                label_tmp=[]
                for i,j in zip(p_idx,p_label):
                    if p_dist[i]<tao:
                        idx_tmp.append(i)
                        label_tmp.append(j)
                    else:
                        p_dist.pop(i)
                        #p_idx.remove(i)
                        #p_label.remove(j)
                        tmp.append(i)
                p_idx = idx_tmp
                p_label = label_tmp
                '''
                tmp = []
                for e in ex_id[cc]:
                    if e == idx:
                        continue
                    #d = np.linalg.norm(fn[e]-fn[idx])
                    a = fn[e] - mu[k]
                    b = c_inv[k]
                    d = np.abs(np.dot(np.dot(a,b),a.T))
                    if d<tao:
                        #print 'added ex with d',d
                        #p_dist[e] = d
                        p_idx.append(e)
                        p_label.append(label[idx])
                        #if label[idx]!=label[e]:
                        #    print input3[e],label[idx], label[e],d
                    else:
                        tmp.append(e)
                #print '# of p label before clean', len(p_label)
                #print '# of p label after clean', len(p_label)
                if not tmp:
                    ex_id.pop(cc)
                else:
                    ex_id[cc] = tmp
                #ex_cur[k] = idx
                ex_al.append([rr,cc,v[0][-2],label[idx],input3[idx]])
                #print cc,label[idx],input3[idx]
                break
        #print len(km_idx), 'training examples'
        '''
        train_fn = fn[km_idx]
        train_label = label[km_idx]
        clf.fit(train_fn, train_label)
        preds_fn = clf.predict(test_fn)
        preds_train = clf.predict(fn[train])
        acc = accuracy_score(test_label, preds_fn)
        acc_ = accuracy_score(label[train], preds_train)
        print 'acc on test set', acc
        print 'acc on cluster set', acc_
        print 'class count of predicted labels on cluster training ex:\n', ct(preds_train)
        '''
    #for e in ex_al: #print the example detail added on each itr
    #    print e
    #print len(p_idx)
    print '# of p label', len(p_label)
    #print 'final tao', tao
    print cl_id
    #for i,j in zip(p_idx,p_label):
    #    print input3[i], j, label[i], p_dist[i]
    print 'psudo label acc', sum(label[p_idx]==p_label)/float(len(p_label))
    p_acc.append(sum(label[p_idx]==p_label)/float(len(p_label)))
    print '----------------------------------------------------'
    print '----------------------------------------------------'
    #ss = raw_input()
#print len(train_label), 'training examples'
print 'class count of clf training ex:', ct(train_label)
print 'average acc:', [np.mean(i) for i in acc_sum]
print 'average p label acc:', np.mean(p_acc)
tmp = []
for i,j in acc_ave.items():
    tmp.append([i,np.mean(j)])
tmp = sorted(tmp, key=lambda x: x[0])
x = [i[0] for i in tmp]
y = [i[1] for i in tmp]

cm_ = CM(test_label, preds_fn)
cm = normalize(cm_.astype(np.float), axis=1, norm='l1')
fig = pl.figure()
ax = fig.add_subplot(111)
cax = ax.matshow(cm)
fig.colorbar(cax)
for x in xrange(len(cm)):
    for y in xrange(len(cm)):
        ax.annotate(str("%.3f(%d)"%(cm[x][y], cm_[x][y])), xy=(y,x),
                    horizontalalignment='center',
                    verticalalignment='center',
                    fontsize=10)
cm_cls =np.unique(np.hstack((test_label,preds_fn)))
cls = []
for c in cm_cls:
    cls.append(mapping[c])
pl.yticks(range(len(cls)), cls)
pl.ylabel('True label')
pl.xticks(range(len(cls)), cls)
pl.xlabel('Predicted label')
pl.title('Mn Confusion matrix (%.3f)'%acc)
pl.show()

'''
acc_sum = []
for train, test in kf:
    train_label = label[train]
    #print len(np.unique(train_label))
    ex = dd(list)
    oc_idx = []
    for i,j in zip(train_label,train):
        ex[i].append(j)
    for v in ex.values():
        train_fd = fn[v]
        n = 1
        if len(v)>=10:
            #print mapping[k], len(v)
            n = len(v)/10
        c = KMeans(init='k-means++', n_clusters=n, n_init=10)
        c.fit(train_fd)
        rank = dd(list)
        for i,j,k in zip(c_labels, v, np.sort(c.transform(train_fd))):
            rank[i].append([j,k[0]])
        for k,vv in rank.items():
            dist = sorted(vv, key=lambda x: x[-1])
            for i in range(rounds):
                if len(dist) > i:
                    oc_idx.append(dist[i][0])
                    print k, input3[dist[i][0]]
    test_fn = fn[test]
    test_label = label[test]
    train_id = []
    print '=============================='
    for i in oc_idx:
        print mapping[label[i]],':',input3[i]
        train_id.append(i)
        train_fn = fn[train_id]
        train_label = label[train_id]
        clf.fit(train_fn, train_label)
        preds_fn = clf.predict(test_fn)
        acc = accuracy_score(test_label, preds_fn)
    acc_sum.append(acc)
print len(train_label), 'training examples'
print ct(train_label)
print 'acc using oracle centroid ex:', np.mean(acc_sum), np.std(acc_sum)
cm_ = CM(test_label, preds_fn)
cm = normalize(cm_.astype(np.float), axis=1, norm='l1')
fig = pl.figure()
ax = fig.add_subplot(111)
cax = ax.matshow(cm)
fig.colorbar(cax)
for x in xrange(len(cm)):
    for y in xrange(len(cm)):
        ax.annotate(str("%.3f(%d)"%(cm[x][y], cm_[x][y])), xy=(y,x),
                    horizontalalignment='center',
                    verticalalignment='center',
                    fontsize=10)
cm_cls =np.unique(np.hstack((test_label,preds_fn)))
cls = []
for c in cm_cls:
    cls.append(mapping[c])
pl.yticks(range(len(cls)), cls)
pl.ylabel('True label')
pl.xticks(range(len(cls)), cls)
pl.xlabel('Predicted label')
pl.title('Mn Confusion matrix (%.3f)'%acc)
pl.show()
'''
