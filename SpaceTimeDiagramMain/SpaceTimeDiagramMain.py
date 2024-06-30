import csv
import os
import collections
from Continuous_processing_of_csv import count_csv , print_file , make_file_name_list
from Make_Diagram_process import make_diagram
from joblib import Parallel, delayed


if __name__ == "__main__":
    reduce_num = 1 #グラフの描画線の数を(1/reduce_num)台に削減する。グラフの生成速度UP。

    result_path = './resultDiagram'
    os.makedirs(result_path,exist_ok=True) #resultフォルダを作る。既にフォルダが存在していてもエラーにならない
    #doing_path = './処理中'
    #os.makedirs(doing_path,exist_ok=True) #resultフォルダを作る。既にフォルダが存在していてもエラーにならない
    
    #relay_csv()
    total_num_of_csv = count_csv()              #全処理ファイル数を取得
    print("ファイル数" , total_num_of_csv)      #全ファイル数を表示 
    print_file(total_num_of_csv)                #全ファイル名を表示
    

    file_name_list = make_file_name_list()      #ファイル名のリストを生成

    for n in file_name_list:
        make_diagram(n,reduce_num)
####並列生成禁止####
    ####メモリリークを引き起こす####
    #####Parallel(n_jobs = -1)([delayed(make_diagram)(n) for n in file_name_list]) #ファイル名を一つずつ渡して実行する
####並列生成禁止####
    print()
    print("====DONE====")
