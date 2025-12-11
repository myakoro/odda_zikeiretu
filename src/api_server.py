"""
Flask APIサーバー
WebダッシュボードとPythonバックエンドを接続するRESTful API
"""
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timedelta
import csv
import io

app = Flask(__name__, static_folder='../web', static_url_path='')
CORS(app)

DB_PATH = 'data/odds_history.db'

def get_db_connection():
    """データベース接続を取得"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """トップページ"""
    return app.send_static_file('index.html')

@app.route('/api/stats')
def get_stats():
    """ダッシュボード統計情報"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # レース総数
        cursor.execute('SELECT COUNT(*) as count FROM races')
        total_races = cursor.fetchone()['count']
        
        # オッズ記録総数
        cursor.execute('SELECT COUNT(*) as count FROM odds_history')
        total_odds = cursor.fetchone()['count']
        
        # 最終更新時刻
        cursor.execute('SELECT MAX(time_stamp) as last_time FROM odds_history')
        last_update_row = cursor.fetchone()
        last_update = last_update_row['last_time'] if last_update_row['last_time'] else '--:--'
        
        conn.close()
        
        return jsonify({
            'total_races': total_races,
            'total_odds': total_odds,
            'monitor_status': '停止中',  # TODO: 実際の監視状態を取得
            'last_update': last_update
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/races')
def get_races():
    """レース一覧取得"""
    try:
        date = request.args.get('date', '')
        ba_code = request.args.get('ba_code', '')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM races WHERE 1=1'
        params = []
        
        if date:
            query += ' AND date = ?'
            params.append(date)
        
        if ba_code:
            query += ' AND ba_code = ?'
            params.append(ba_code)
        
        query += ' ORDER BY date DESC, race_no ASC'
        
        cursor.execute(query, params)
        races = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify(races)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/odds/<race_id>')
def get_odds(race_id):
    """特定レースのオッズ履歴取得"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM odds_history 
            WHERE race_id = ? 
            ORDER BY umaban, time_stamp
        ''', (race_id,))
        
        odds_data = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify(odds_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fetch-historical', methods=['POST'])
def fetch_historical():
    """過去データ取得開始"""
    try:
        data = request.json
        service_key = data.get('service_key', 'UNKNOWN')
        days = data.get('days', 7)
        
        # TODO: collector.pyを別スレッドで実行
        # 現在は簡易実装
        
        return jsonify({'success': True, 'message': f'{days}日分のデータ取得を開始しました'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/start-monitor', methods=['POST'])
def start_monitor():
    """リアルタイム監視開始"""
    try:
        data = request.json
        data_type = data.get('data_type', '0B12')
        
        # TODO: realtime_monitor.pyを別スレッドで実行
        
        return jsonify({'success': True, 'message': 'リアルタイム監視を開始しました'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stop-monitor', methods=['POST'])
def stop_monitor():
    """リアルタイム監視停止"""
    try:
        # TODO: 監視スレッドを停止
        
        return jsonify({'success': True, 'message': 'リアルタイム監視を停止しました'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export-csv')
def export_csv():
    """データをCSVでエクスポート"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                oh.race_id,
                r.race_name,
                r.date,
                oh.time_stamp,
                oh.umaban,
                oh.odds_tan,
                oh.odds_fuku_min,
                oh.odds_fuku_max,
                oh.popularity
            FROM odds_history oh
            LEFT JOIN races r ON oh.race_id = r.race_id
            ORDER BY oh.race_id, oh.umaban, oh.time_stamp
        ''')
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # ヘッダー
        writer.writerow(['レースID', 'レース名', '日付', '時刻', '馬番', '単勝オッズ', '複勝下限', '複勝上限', '人気'])
        
        # データ
        for row in cursor.fetchall():
            writer.writerow(row)
        
        conn.close()
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'odds_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("投資競馬オッズ分析システム - APIサーバー")
    print("=" * 60)
    print("\nWebダッシュボード: http://localhost:5000")
    print("Ctrl+C で停止\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
