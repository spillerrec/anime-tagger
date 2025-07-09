import { getCustomTags, getHistogramForTag } from './api'

export function runProgressBar(containerId, guid) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container with ID "${containerId}" not found.`);
        return;
    }

    // Create progress bar elements
    container.innerHTML = `
        <div style="border: 1px solid #ccc; border-radius: 5px; width: 100%; background: #f0f0f0; height: 30px; position: relative;">
            <div id="${containerId}-bar" style="background: #4caf50; width: 0%; height: 100%; border-radius: 5px 0 0 5px;"></div>
        </div>
        <div id="${containerId}-info" style="margin-top: 8px; font-family: sans-serif; font-size: 14px;"></div>
    `;

    const bar = document.getElementById(`${containerId}-bar`);
    const info = document.getElementById(`${containerId}-info`);

    async function updateProgress() {
        try {
            const response = await fetch(`/progress/${guid}`);
            if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
            const data = await response.json();

            console.log(data)
            const { n, total, elapsed, rate } = data;
            const percentage = total > 0 ? (n / total) * 100 : 0;
            bar.style.width = `${percentage}%`;

            const remaining = rate > 0 ? ((total - n) / rate).toFixed(1) : '∞';

            info.textContent = `Processed ${n} of ${total} items. Elapsed: ${elapsed.toFixed(1)}s, Remaining time: ${remaining}s`;

            if (n < total) {
                setTimeout(updateProgress, 1000);
            } else {
                info.textContent += ' ✅ Done.';
            }

        } catch (err) {
            console.error('Error fetching progress:', err);
            info.textContent = '⚠️ Error retrieving progress data.';
        }
    }

    updateProgress();
}