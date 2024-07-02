import csv
import os
import collections
from decimal import Decimal
import matplotlib.pyplot as plt
import matplotlib as mpl
import time
import pandas as pd
from joblib import Parallel, delayed
import tqdm_joblib as tj
from tqdm import tqdm
import matplotlib.style as mplstyle
from matplotlib import gridspec
import gc

#    #カレントディレクトリは省略可能だが明示したい場合は「.」で表し、一階層上位のディレクトリは「..」で表す。「..」を繰り返し記述することでディレクトリ階層の親子関係をたどって上へ移動することができる。
#    #「../../foo/bar.txt」という記述は、現在のディレクトリの二階層上のディレクトリの中にある「foo」ディレクトリの中にある「bar.txt」というファイルを指し示している。
#CHANGED ヘッダーの要素数が異なっていたので，それぞれ対応する番号に書き換えている
#CHANGED Original : time, ID,前方位置(position?),後方位置,道路ID,車線,speed,加速度,車間,相対速度,,,,,etc
#CHANGED SUMO : time, ID, position, speed
#CHANGED つまり要素番号 time:変更なし ID:変更なし positon:変更なし speed:6->3

def make_diagram(csv_name,reduce_num):
    '''
    ファイル名を受け取って、それについてパスを生成。その後グラフを作成
    '''
    time_sta = time.time()

    #========ここからcsvのデータ作成================================================
    f_name = csv_name[:-4]     #グラフのファイル名生成用
    file_pass = ".\元データ\\" + csv_name #生データフォルダ内の一つ目のcsvファイルを読み込む

    #読み込んだcsvのデータを保持する配列（生データ）
    data = []

    with open(file_pass, 'r', encoding="utf-8", errors="", newline="") as f:
        #リスト形式
        csv_data1 = csv.reader(f, delimiter=",", doublequote=True, lineterminator="\r\n", quotechar='"', skipinitialspace=True)

        #辞書形式
        #f = csv.DictReader(csv_data1, delimiter=",", doublequote=True, lineterminator="\r\n", quotechar='"', skipinitialspace=True)

        data_append = data.append
        for i in csv_data1:  # 各行がリストになっている
            data_append(i)
            #print(i)
    #========ここまでcsvのデータ作成================================================


    #========ここから台数と車両IDの最大値を得る============================================
    car_list= [row[1] for row in data]
    car_list.remove('ID') #ヘッダーも含まれてしまうので削除
    c = set(collections.Counter(car_list)) #重複を削除,IDリストになる
    car_num= len(c) #車の台数
    #========ここまで台数と車両IDの最大値を得る============================================


    #===================ここから車両IDを0から順に辞書型に登録する=======================
    car_dict = {}
    for i in c:
        car_dict[i] = i
    #===================ここまで車両IDを0から順に辞書型に登録する=======================


    #=========ここから車両ID別データに分類========================================================
    # carData  = [[[0] * 21 for i in range(0)] for j in range(car_num)]#車の台数分用意 
    carData = {}
    
    for i in range(1,len(data)):#ヘッダーは除外してインクリメント
        #車両IDを見て、対応する配列に一行ずつ丸々追加
        carData.setdefault(data[i][1], []).append(data[i])
    #=========ここまで車両ID別データに分類========================================================


    #========ここからシミュレーションの開始時間・終了時間を取得====================================================================
    sim_start_time: int = 0
    sim_finish_time: int  = 0

    sim_start_time = int(float(data[1][0]))

    sim_finish_time=int(float(data[len(data)-1][0]))
    #========ここまでシミュレーションの開始時間・終了時間を取得====================================================================


    #========ここからx軸作成========================================================
    x = [0] * (sim_finish_time - sim_start_time + 1)
    for i in range(sim_finish_time - sim_start_time + 1):
        x[i] = sim_start_time + i
    #========ここまでx軸作成========================================================


    #========ここからy軸作成========================================================
    
    # y = [[None] * (sim_finish_time - sim_start_time + 1) for k in range(car_num)]
    y = {key: [None] * (sim_finish_time - sim_start_time + 1) for key in c}

    for k in c:
        start_i = int(float(carData[k][0][0]))
        for i in range(len(carData[k])):
            y[k][start_i - sim_start_time + i] = float(carData[k][i][2])        
    #========ここまでy軸作成========================================================


#==================ここからグラフ描画======================
    mplstyle.use('fast')#これを書いておくと早くなるらしいが、効果を感じられない

    #図を二つ作成（グラフとカラーバー）
    fig = plt.figure()
    #width_ratiosでグラフ表示エリア比率を変える
    spec = gridspec.GridSpec(ncols=2, nrows=1, width_ratios=[50, 2])
    ax1 = fig.add_subplot(spec[0])
    ax2 = fig.add_subplot(spec[1])
    #グラフタイトル作成
    str_size = len(f_name)
    graph_title = f_name[:str_size - 54] + '\n' + f_name[-54:]
    fig.suptitle(graph_title, fontname="MS Gothic") 
 
    #軸ラベル
    ax1.set_xlabel("時間[s]", fontname="MS Gothic")
    ax1.set_ylabel("距離[m]", fontname="MS Gothic")

    colors = get_color_list()#ヒートマップ色にするためのカラーリストを指定

    count=0
    #手法1=================
    for i in tqdm(c):
        ##並列で処理
        #Parallel(n_jobs = 1)([delayed(draw_line)(j,x,y[i],ax1,colors) for j in range(len(x)-1)])
        ##直列で処理
        if count%reduce_num==0:
            for j in range(len(x)-1):
                draw_line(j,x,y[i],ax1,colors)
        count+=1
    #手法2=================
    #with tj.tqdm_joblib((len(x)-1)*(len(list(range(0,car_num,reduce_num))))):
    #    #1でないと何故かエラーになる。たぶん二重ループの並列化だからだと思う。
    #    Parallel(n_jobs = 1)([delayed(draw_line)(j,x,y[i],ax1,colors) for j in range(len(x)-1) for i in range(0,car_num,reduce_num)])

    #軸の最小値と最大値を設定
    ax1.set_xlim(left=sim_start_time)
    ax1.set_ylim(bottom=0, top=15000)

#==================ここまでグラフ描画======================

#==================ここからオリジナルカラーマップのグラフを作成======================
    #明度の列を全て1で追加
    colors['A'] = 1.0
    #自作のカラーマップ
    segment_data = make_segment_data()#セグメントデータをRGBで指定
    cmap = mpl.colors.LinearSegmentedColormap('nipy_spectral_r', segment_data)#カラーマップにする 

    norm = mpl.colors.Normalize(vmin=40, vmax=100)#カラーバーの下限と上限
    #cmap=plt.cm.jet#デフォルトの虹色指定のcbarの引数
    #fig, ax2 = plt.subplots()
    cbar = mpl.colorbar.ColorbarBase(
        ax=ax2,
        cmap=cmap,
        norm=norm,
        orientation="vertical",
        label="Match number",
    )
#==================ここまでオリジナルカラーマップのグラフを作成======================

    #plt.show()#出力画像確認
    #出力
    print("The graph is being output now. Please wait...")
    result_path = './resultDiagram'
    save_name = result_path + "\\" + f_name + ".png"
    fig.savefig(save_name, format="png", dpi=350)
    #plt.show()

    #メモリの解放
    plt.clf()
    plt.close()
    gc.collect()

    print()
    time_end = time.time()
    tim = time_end - time_sta

    print("===============" , csv_name , "処理終了===============")
    print("[全車両台数: ",car_num,", 開始時間：" , sim_start_time,", 終了時間：" , sim_finish_time,"] 作成時間：" , '{:.3f}'.format(tim) , "s")


def get_color_list():
    '''
    1001種類の虹色をDataFrameで返す。
    '''
    index= list(range(0,1000,1))
    column=['R', 'G', 'B']
    colors = pd.DataFrame(index = index,columns=column, dtype='float64') #グラデーションのrgbを順に格納
    colors.loc[0]    = [204,204,204]
    colors.loc[111]  = [220,0  ,0  ]
    colors.loc[222]  = [255,165,0  ]
    colors.loc[333]  = [212,247,0  ]
    colors.loc[444]  = [0,  228,0  ]
    colors.loc[555]  = [0  ,154,0  ]
    colors.loc[666]  = [0  ,166,183]
    colors.loc[777]  = [0  ,56 ,221]
    colors.loc[888]  = [109,0  ,156]
    colors.loc[1000] = [0  ,0  ,0  ]
    colors = colors.interpolate(limit_direction='both') #欠損位置は線形補完
    colors = colors/255 #正規化

    return colors

def make_segment_data():
    '''
    オリジナルのカラーマップのセグメントデータを作成する
    灰・赤・橙・黄・緑・青・紺・紫・黒
    '''
    segment_data = {    
    'red':
        [
            (0.000, 204/255, 204/255),
            (0.111, 220/255, 220/255),
            (0.222, 255/255, 255/255),
            (0.333, 212/255, 212/255),
            (0.444,   0/255,   0/255),
            (0.555,   0/255,   0/255),
            (0.666,   0/255,   0/255),
            (0.777,   0/255,   0/255),
            (0.888, 109/255, 109/255),
            (1.000,   0/255,   0/255),
        ],
    'green':
        [
            (0.000, 204/255, 204/255),
            (0.111,   0/255,   0/255),
            (0.222, 165/255, 165/255),
            (0.333, 247/255, 247/255),
            (0.444, 228/255, 228/255),
            (0.555, 154/255, 154/255),
            (0.666, 166/255, 166/255),
            (0.777,  56/255,  56/255),
            (0.888,   0/255,   0/255),
            (1.000,   0/255,   0/255),
        ],
    'blue':
        [
            (0.000, 204/255, 204/255),
            (0.111,   0/255,   0/255),
            (0.222,   0/255,   0/255),
            (0.333,   0/255,   0/255),
            (0.444,   0/255,   0/255),
            (0.555,   0/255,   0/255),
            (0.666, 183/255, 183/255),
            (0.777, 221/255, 221/255),
            (0.888, 156/255, 156/255),
            (1.000,   0/255,   0/255),
        ],
    'alpha':
        [
            (0.000, 1.0, 1.0),
            (0.111, 1.0, 1.0),
            (0.222, 1.0, 1.0),
            (0.333, 1.0, 1.0),
            (0.444, 1.0, 1.0),
            (0.555, 1.0, 1.0),
            (0.666, 1.0, 1.0),
            (0.777, 1.0, 1.0),
            (0.888, 1.0, 1.0),
            (1.000, 0.0, 0.0),
        ]
}

    return segment_data

def draw_line(j,x,y,ax,colors):
    #1秒間の平均速度から色を決める
    # if x[j]!=None and x[j+1]!=None and y[j]!=None and y[j+1]!=None:#計算可能な場合
    #     ave_vel = ((y[j+1]-y[j])/(x[j+1] - x[j]))*3.66666 #時速を計算
    #     if ave_vel>=0: 
    #         color_num = int((ave_vel/130)*1000)#0km/hから130km/hを0から1000の間に正規化
    #         try:#速度が0から130km/hのとき
    #             Color=tuple(colors.loc[color_num])
    #         except:#速度が正規化の範囲から溢れた場合は黒
    #             Color=tuple(colors.loc[1000])
    #         ax.plot(x[j:j+2], y[j:j+2], color=Color, lw=0.2)
    # else:#計算できないときは黒
    #     Color=tuple(colors.loc[1000])
    
    if x[j]!=None and x[j+1]!=None and y[j]!=None and y[j+1]!=None:#計算可能な場合
        ave_vel = ((y[j+1]-y[j])/(x[j+1] - x[j]))*3.66666 #時速を計算
        if y[j-1]!=None: 
            if y[j-1]<y[j]<y[j+1]:
                color_num = int((ave_vel/100)*1000)#* 0km/hから100km/hを0から1000の間に正規化
                try:#速度が0から130km/hのとき
                    Color=tuple(colors.loc[color_num])
                except:#速度が正規化の範囲から溢れた場合は透明
                    Color=tuple(colors.loc[1000])
                ax.plot(x[j:j+2], y[j:j+2], color=Color, lw=0.2)