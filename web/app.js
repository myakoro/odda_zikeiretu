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

// グローバル変数: Chart.jsインスタンス
let oddsChart = null;
let currentOddsData = null;
let currentDisplayMode = 'both';

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
            document.getElementById('odds-toggle-buttons').style.display = 'none';
            document.getElementById('chart-legend').style.display = 'none';
            document.getElementById('chart-wrapper').style.display = 'none';
            return;
        }
        
        // データを保存
        currentOddsData = oddsData;
        
        // UI要素を表示
        document.getElementById('odds-toggle-buttons').style.display = 'flex';
        document.getElementById('chart-legend').style.display = 'flex';
        document.getElementById('chart-wrapper').style.display = 'block';
        
        // グラフを描画
        renderOddsChart(oddsData);
        
        // 馬番ごとにグループ化してサマリー表示
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
                    <p>最新単勝オッズ: <strong>${latest.odds_tan.toFixed(1)}</strong>倍</p>
                    <p>最新複勝オッズ: <strong>${latest.odds_fuku_min.toFixed(1)} - ${latest.odds_fuku_max.toFixed(1)}</strong>倍</p>
                    <p>初回オッズ: ${first.odds_tan.toFixed(1)}倍 → 変動率: <span style="color: ${change > 0 ? 'var(--danger-color)' : 'var(--success-color)'};}">${change > 0 ? '+' : ''}${change}%</span></p>
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

// オッズグラフ描画
function renderOddsChart(oddsData) {
    // 馬番ごとにグループ化
    const groupedByUmaban = {};
    oddsData.forEach(record => {
        if (!groupedByUmaban[record.umaban]) {
            groupedByUmaban[record.umaban] = [];
        }
        groupedByUmaban[record.umaban].push(record);
    });
    
    // 馬番でソート
    const sortedUmabans = Object.keys(groupedByUmaban).sort((a, b) => parseInt(a) - parseInt(b));
    
    // 最初の馬番のデータからタイムスタンプを取得
    const firstUmaban = sortedUmabans[0];
    const timestamps = groupedByUmaban[firstUmaban].map(record => record.time_stamp);
    
    // データセットを作成
    const datasets = [];
    
    // 色のパレット
    const colors = [
        '#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
        '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'
    ];
    
    sortedUmabans.forEach((umaban, index) => {
        const records = groupedByUmaban[umaban];
        const color = colors[index % colors.length];
        
        // 単勝オッズデータセット
        datasets.push({
            label: `${umaban}番 単勝`,
            data: records.map(r => r.odds_tan),
            borderColor: color,
            backgroundColor: 'transparent',
            borderWidth: 2,
            pointRadius: 3,
            pointHoverRadius: 5,
            tension: 0.1,
            hidden: false,
            oddsType: 'tan',
            umaban: umaban
        });
        
        // 複勝オッズ下限データセット
        datasets.push({
            label: `${umaban}番 複勝下限`,
            data: records.map(r => r.odds_fuku_min),
            borderColor: color,
            backgroundColor: 'transparent',
            borderWidth: 2,
            borderDash: [5, 5],
            pointRadius: 0,
            tension: 0.1,
            hidden: false,
            oddsType: 'fuku',
            umaban: umaban,
            fill: '+1'
        });
        
        // 複勝オッズ上限データセット
        datasets.push({
            label: `${umaban}番 複勝上限`,
            data: records.map(r => r.odds_fuku_max),
            borderColor: color,
            backgroundColor: color + '33',
            borderWidth: 2,
            borderDash: [5, 5],
            pointRadius: 0,
            tension: 0.1,
            hidden: false,
            oddsType: 'fuku',
            umaban: umaban,
            fill: false
        });
    });
    
    // 既存のチャートを破棄
    if (oddsChart) {
        oddsChart.destroy();
    }
    
    // チャートを作成
    const ctx = document.getElementById('odds-analysis-chart').getContext('2d');
    oddsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timestamps,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#f1f5f9',
                    bodyColor: '#f1f5f9',
                    borderColor: '#334155',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: '時刻',
                        color: '#94a3b8'
                    },
                    ticks: {
                        color: '#94a3b8',
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: {
                        color: '#334155'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'オッズ',
                        color: '#94a3b8'
                    },
                    ticks: {
                        color: '#94a3b8'
                    },
                    grid: {
                        color: '#334155'
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// オッズ表示切り替え
function toggleOddsDisplay(mode) {
    if (!oddsChart) return;
    
    currentDisplayMode = mode;
    
    // ボタンのアクティブ状態を更新
    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.mode === mode) {
            btn.classList.add('active');
        }
    });
    
    // データセットの表示/非表示を切り替え
    oddsChart.data.datasets.forEach(dataset => {
        if (mode === 'both') {
            dataset.hidden = false;
        } else if (mode === 'tan') {
            dataset.hidden = dataset.oddsType !== 'tan';
        } else if (mode === 'fuku') {
            dataset.hidden = dataset.oddsType !== 'fuku';
        }
    });
    
    oddsChart.update();
}
