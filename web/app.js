// タブ切り替え機能
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const targetTab = btn.dataset.tab;
        
        // すべてのタブとコンテンツから active クラスを削除
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // クリックされたタブとコンテンツに active クラスを追加
        btn.classList.add('active');
        document.getElementById(targetTab).classList.add('active');
    });
});

// ページ読み込み時の初期化
window.addEventListener('DOMContentLoaded', () => {
    loadDashboardStats();
    setInterval(loadDashboardStats, 5000); // 5秒ごとに更新
});

// ダッシュボード統計情報の読み込み
async function loadDashboardStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        document.getElementById('total-races').textContent = data.total_races || 0;
        document.getElementById('total-odds').textContent = data.total_odds || 0;
        document.getElementById('monitor-status').textContent = data.monitor_status || '停止中';
        document.getElementById('last-update').textContent = data.last_update || '--:--';
    } catch (error) {
        console.error('統計情報の取得に失敗:', error);
    }
}

// レース一覧の読み込み
async function loadRaces() {
    const date = document.getElementById('race-date').value;
    const baCode = document.getElementById('ba-filter').value;
    
    if (!date) {
        alert('日付を選択してください');
        return;
    }
    
    try {
        const params = new URLSearchParams({ date, ba_code: baCode });
        const response = await fetch(`/api/races?${params}`);
        const races = await response.json();
        
        const raceList = document.getElementById('race-list');
        
        if (races.length === 0) {
            raceList.innerHTML = '<p class="empty-state">該当するレースが見つかりませんでした</p>';
            return;
        }
        
        raceList.innerHTML = races.map(race => `
            <div class="race-card" style="background: var(--bg-hover); padding: 20px; margin-bottom: 15px; border-radius: 10px; cursor: pointer;" onclick="viewRaceDetails('${race.race_id}')">
                <h3>${race.race_name}</h3>
                <p>レースID: ${race.race_id} | 発走時刻: ${race.start_time}</p>
            </div>
        `).join('');
    } catch (error) {
        console.error('レース一覧の取得に失敗:', error);
        alert('レース一覧の取得に失敗しました');
    }
}

// レース詳細表示
function viewRaceDetails(raceId) {
    document.getElementById('analysis-race-id').value = raceId;
    document.querySelector('[data-tab="analysis"]').click();
    analyzeRace();
}

// オッズ分析
async function analyzeRace() {
    const raceId = document.getElementById('analysis-race-id').value;
    
    if (!raceId) {
        alert('レースIDを入力してください');
        return;
    }
    
    try {
        const response = await fetch(`/api/odds/${raceId}`);
        const oddsData = await response.json();
        
        const resultDiv = document.getElementById('analysis-result');
        
        if (oddsData.length === 0) {
            resultDiv.innerHTML = '<p class="empty-state">オッズデータが見つかりませんでした</p>';
            return;
        }
        
        // 馬番ごとにグループ化
        const groupedByUmaban = {};
        oddsData.forEach(record => {
            if (!groupedByUmaban[record.umaban]) {
                groupedByUmaban[record.umaban] = [];
            }
            groupedByUmaban[record.umaban].push(record);
        });
        
        let html = '<h3>オッズ変動履歴</h3>';
        
        for (const [umaban, records] of Object.entries(groupedByUmaban)) {
            const latest = records[records.length - 1];
            const first = records[0];
            const change = ((latest.odds_tan - first.odds_tan) / first.odds_tan * 100).toFixed(1);
            
            html += `
                <div style="background: var(--bg-dark); padding: 15px; margin: 10px 0; border-radius: 10px;">
                    <h4>${umaban}番 (人気: ${latest.popularity}位)</h4>
                    <p>最新オッズ: <strong>${latest.odds_tan.toFixed(1)}</strong>倍</p>
                    <p>初回オッズ: ${first.odds_tan.toFixed(1)}倍 → 変動率: <span style="color: ${change > 0 ? 'var(--danger-color)' : 'var(--success-color)'};">${change > 0 ? '+' : ''}${change}%</span></p>
                    <p>記録数: ${records.length}件</p>
                </div>
            `;
        }
        
        resultDiv.innerHTML = html;
    } catch (error) {
        console.error('オッズ分析に失敗:', error);
        alert('オッズ分析に失敗しました');
    }
}

// 過去データ取得
async function fetchHistoricalData() {
    const serviceKey = document.getElementById('service-key').value;
    const days = document.getElementById('fetch-days').value;
    
    if (!serviceKey || serviceKey === '') {
        alert('サービスキーを入力してください');
        return;
    }
    
    try {
        const response = await fetch('/api/fetch-historical', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ service_key: serviceKey, days: parseInt(days) })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(`過去データの取得を開始しました（${days}日分）`);
        } else {
            alert('データ取得に失敗しました: ' + result.error);
        }
    } catch (error) {
        console.error('過去データ取得に失敗:', error);
        alert('過去データ取得に失敗しました');
    }
}

// リアルタイム監視開始
async function startMonitoring() {
    const monitorType = document.getElementById('monitor-type').value;
    
    try {
        const response = await fetch('/api/start-monitor', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data_type: monitorType })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('リアルタイム監視を開始しました');
            document.getElementById('monitor-status').textContent = '監視中';
        } else {
            alert('監視開始に失敗しました: ' + result.error);
        }
    } catch (error) {
        console.error('監視開始に失敗:', error);
        alert('監視開始に失敗しました');
    }
}

// リアルタイム監視停止
async function stopMonitoring() {
    try {
        const response = await fetch('/api/stop-monitor', { method: 'POST' });
        const result = await response.json();
        
        if (result.success) {
            alert('リアルタイム監視を停止しました');
            document.getElementById('monitor-status').textContent = '停止中';
        } else {
            alert('監視停止に失敗しました');
        }
    } catch (error) {
        console.error('監視停止に失敗:', error);
        alert('監視停止に失敗しました');
    }
}

// データエクスポート
async function exportData() {
    try {
        window.location.href = '/api/export-csv';
        alert('データをエクスポートしています...');
    } catch (error) {
        console.error('エクスポートに失敗:', error);
        alert('エクスポートに失敗しました');
    }
}
