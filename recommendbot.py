from __future__ import division, print_function
from theano.sandbox import cuda
import utils; reload(utils)
from utils import *

from sqlalchemy import create_engine
import MySQLdb

n_factors = 50
np.random.seed = 42

model_path = 'models/'
if not os.path.exists(model_path): os.mkdir(model_path)
batch_size=10


    
def input_table():
    db = MySQLdb.connect("localhost","root","","order_easy" )
    df_mysql = pd.read_sql('select * from review;', con=db)
    pd.DataFrame.to_csv(df_mysql,"rating_final.csv",index=False)
    cur=db.cursor()
    cur.execute("SELECT COUNT(*) FROM food_items")
    n=cur.fetchone()
    return n[0]
        
        
def input_csv():
    ratings = pd.read_csv('rating_final.csv')
    ratings['foodID']=ratings['foodID'].replace(0,np.nan)
        
    users = ratings.userID.unique()
    food = ratings.foodID.unique()

    userid2idx = {o:i for i,o in enumerate(users)}
    foodid2idx = {o:i for i,o in enumerate(food)}

    ratings.foodID = ratings.foodID.apply(lambda x: foodid2idx[x])
    ratings.userID = ratings.userID.apply(lambda x: userid2idx[x])

    user_min, user_max, food_min, food_max = (ratings.userID.min(), 
                                                  ratings.userID.max(), ratings.foodID.min(), ratings.foodID.max())

    n_users = ratings.userID.nunique()
    n_food = ratings.foodID.nunique()

        

    msk = np.random.rand(len(ratings)) < 0.9
    trn = ratings[msk]
    val = ratings[~msk]
    return trn,val, n_users, n_food, userid2idx, foodid2idx

def embedding_input(name, n_in, n_out, reg):
    inp = Input(shape=(1,), dtype='int64', name=name)
    return inp, Embedding(n_in, n_out, input_length=1, W_regularizer=l2(reg))(inp)
    
def train_model(trn,val, n_users, n_food):
    user_in, u = embedding_input('user_in', n_users, n_factors, 1e-4)
    food_in, f = embedding_input('place_in', n_food, n_factors, 1e-4)

    x = merge([u, f], mode='concat')
    x = Flatten()(x)
    x = Dropout(0.3)(x)
    x = Dense(70, activation='relu')(x)
    x = Dropout(0.75)(x)
    x = Dense(1)(x)
    nn = Model([user_in, food_in], x)
    nn.compile(Adam(0.001), loss='mse')

    nn.fit([trn.userID, trn.foodID], trn.rating, batch_size=10, nb_epoch=16, 
               validation_data=([val.userID, val.foodID], val.rating))

    nn.save_weights(model_path+'nn.h5')
    return nn
        
def get_recommendation(count,userid2idx,nn,foodid2idx):
    nn.load_weights(model_path+'nn.h5')
    a=[]
    i=0
    foodid2idx2 = {o:i for i,o in foodid2idx.items()}
    db = MySQLdb.connect("localhost","root","","order_easy" )
    cur=db.cursor()
    cur.execute("TRUNCATE TABLE recommender")
    for k,v in userid2idx.items():
        a=nn.predict([int(v)*np.ones(137),np.arange(count)])
        a=np.argsort(a,axis=0)[::-1]
        for j in a[:20]:
            cur.execute("""INSERT INTO recommender values(%s,%s)""",(k,foodid2idx2[j[0]]))
        
        i+=1
    db.commit()
        
