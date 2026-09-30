import json
import pandas as pd
import matplotlib.pyplot as plt

def main():
    records = []
    with open("data/logs.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    
    if not records:
        print("No data found!")
        return

    df = pd.DataFrame(records)
    df['ts'] = pd.to_datetime(df['ts'])

    df_responses = df[df['event'] == 'response_sent'].copy()
    df_requests = df[df['event'] == 'request_received'].copy()

    fig, axs = plt.subplots(3, 2, figsize=(15, 12))
    fig.suptitle("Monitoring Dashboard (Last 60 Minutes)", fontsize=16)

    # 1. Latency
    if not df_responses.empty:
        df_resp_idx = df_responses.set_index('ts')
        df_resp_idx[['latency_ms', 'ttft_ms']].plot(ax=axs[0, 0])
        axs[0, 0].axhline(y=3000, color='r', linestyle='--', label='SLO 3000ms')
    axs[0, 0].set_title("Latency & TTFT (ms)")
    axs[0, 0].legend()

    # 2. Traffic
    if not df_requests.empty:
        df_req_idx = df_requests.set_index('ts')
        df_req_idx.resample('1min').size().plot(ax=axs[0, 1])
    axs[0, 1].set_title("Traffic (Req/min)")

    # 3. Errors (Retrieval Success rate)
    df_tool = df.dropna(subset=['tool_success']).copy()
    if not df_tool.empty:
        df_tool['tool_success'] = df_tool['tool_success'].astype(float)
        df_tool_idx = df_tool.set_index('ts')
        success_rate = df_tool_idx.resample('1min')['tool_success'].mean() * 100
        success_rate.plot(ax=axs[1, 0], marker='o')
        axs[1, 0].axhline(y=90, color='r', linestyle='--', label='SLO 90%')
    axs[1, 0].set_title("Retrieval Success Rate (%)")
    axs[1, 0].set_ylim(0, 110)
    axs[1, 0].legend()

    # 4. Cost
    if not df_responses.empty:
        df_responses.set_index('ts')['cost_usd'].cumsum().plot(ax=axs[1, 1])
    axs[1, 1].set_title("Cumulative Cost (USD)")

    # 5. Tokens
    if not df_responses.empty:
        df_responses.set_index('ts')[['tokens_in', 'tokens_out']].plot(ax=axs[2, 0])
    axs[2, 0].set_title("Tokens Usage")

    # 6. Quality
    if not df_responses.empty:
        df_responses.set_index('ts')['quality_score'].plot(ax=axs[2, 1], marker='o')
        axs[2, 1].axhline(y=0.75, color='r', linestyle='--', label='SLO 0.75')
    axs[2, 1].set_title("Quality Score")
    axs[2, 1].set_ylim(0, 1.1)
    axs[2, 1].legend()

    plt.tight_layout()
    plt.savefig("submission/evidence/11-dashboard-overview.png")
    print("Dashboard saved to submission/evidence/11-dashboard-overview.png")

if __name__ == "__main__":
    main()
