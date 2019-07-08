import pandas as pd


def mem_usage(pandas_obj):
    if isinstance(pandas_obj,pd.DataFrame):
        usage_b = pandas_obj.memory_usage(deep=True).sum()
    else:
        usage_b = pandas_obj.memory_usage(deep=True)
    usage_mb = usage_b/1024**2
    return "{:03.2f}MB".format(usage_mb)


def optimize_memory(df):
    for col in ['appid','use_date']:
        df[col] = df[col].astype('category')
    df['uid'] = df['uid'].astype('uint32')
    for col in ['duration','times']:
        df[col] = df[col].astype('float32')
    return df

reader = pd.read_csv('../data/user_app_usage.csv',iterator=True,names=['uid','appid','duration','times','use_date'])
chunkSize = 100000000
loop = True
allchunk = pd.DataFrame()
while loop:
    try:
        chunk = reader.get_chunk(chunkSize)
        chunk = optimize_memory(chunk)
        chunk.drop(columns=['use_date'],axis=1,inplace=True)
        chunk['duration_average'] = chunk['duration']/chunk['times']
        print(len(chunk),mem_usage(chunk))

        for col in ['duration','times','duration_average']:
            _ = chunk.groupby(['uid','appid'],as_index=False)[col].agg({col+'_max':'max',col+'_min':'min',col+'_mean':'mean'})
            chunk = chunk.merge(_,on=['uid','appid'],how='left')
            chunk.drop(columns=[col],axis=1,inplace=True)

        print(len(chunk))
        chunk = chunk.drop_duplicates(['uid','appid'])
        print(len(chunk))
        allchunk = pd.concat([allchunk,chunk],ignore_index=True)
        print("allchunk:",len(allchunk),mem_usage(allchunk))
    except StopIteration:
        loop = False
        print("Iteration is stopped")

for col in ['duration_max','duration_min','duration_mean','times_max','times_min','times_mean',
            'duration_average_max','duration_average_min','duration_average_mean']:
    _ = allchunk.groupby(['uid','appid'],as_index=False)[col].agg({col+'_'+col.split('_')[-1]:col.split('_')[-1]})
    allchunk = allchunk.merge(_,on=['uid','appid'],how='left')
    allchunk.drop(columns=[col],inplace=True)



allchunk = allchunk.drop_duplicates(['uid','appid'])
allchunk = allchunk.rename(columns={'duration_max_max':'duration_max','duration_min_min':'duration_min','duration_mean_mean':'duration_mean',
                         'times_max_max':'times_max','times_min_min':'times_min','times_mean_mean':'times_mean',
                        'duration_average_max_max':'duration_average_max','duration_average_min_min':'duration_average_min','duration_average_mean_mean':'duration_average_mean'
                         })
print(len(allchunk))

allchunk.to_csv('../data/user_app_usage_feature_reset.csv', index=False)