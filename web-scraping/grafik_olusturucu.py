import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import glob

# SETUP
current_folder = os.getcwd()
graphs_folder = os.path.join(current_folder, "Graphs")
csv_folder = os.path.join(current_folder, "CSVs")

search_path = os.path.join(csv_folder, "*.csv")
csv_files = glob.glob(search_path)

print(f"{len(csv_files)} csv dosyasi bulundu. İşleme başlatiliyor...")

# MAIN LOOP
for filepath in csv_files:
    try:
        filename = os.path.basename(filepath) # Eg. "TARANTULA_SILK_dataset.csv"

        df = pd.read_csv(filepath) # Loads data to DataFrame

        # Convert text date to real Time Object
        df['datetime'] = pd.to_datetime(df['readable_date'])
        df = df.sort_values('datetime')

        # Round prices to 1 decimal place
        df['sellPrice'] = df['sellPrice'].round(1)
        df['buyPrice'] = df['buyPrice'].round(1)

        # Create graph canvas
        fig, ax1 = plt.subplots(figsize=(12,6))

        # Title
        item_name = filename.replace(".csv", "").replace("_", " ").title()
        plt.title(f"{item_name}")

        ax1.set_xlabel('Time')

        # LEFT AXIS (Prices)
        ax1.set_ylabel("Price (Coins)", color="black", fontweight="bold")

        # Line 1: Sell Price (Red)
        line1, = ax1.plot(df['datetime'], df["sellPrice"], color='red', label="Sell Price", linewidth=1.5)

        # Line 2: Buy Price (Green)
        line2, = ax1.plot(df['datetime'], df["buyPrice"], color='green', label="Buy Price", linewidth=1.5)

        ax1.tick_params(axis='y', labelcolor='black')

        # RIGHT AXIS (Volume)
        ax2 = ax1.twinx()
        ax2.set_ylabel("Volume (Items)", color="darkblue", fontweight="bold")

        # Line 3: Sell Price (Purple)
        line3, = ax2.plot(df['datetime'], df["sellVolume"], color='purple', label="Sell Volume", linestyle="--", alpha=0.6)

        # Line 4: Buy Price (Blue)
        line4, = ax2.plot(df['datetime'], df["buyVolume"], color='blue', label="Buy Volume", linestyle="--", alpha=0.6)

        ax2.tick_params(axis="y", labelcolor="darkblue")

        # FORMATTING
        # Combine legends
        lines = [line1, line2, line3, line4]
        labels = [line.get_label() for line in lines]
        ax1.legend(lines, labels, loc="upper left", frameon=True)

        # Format X-axis Dates (Hour:Minute)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        fig.autofmt_xdate()
        ax1.grid(True, linestyle=":", alpha=0.6)

        # SAVE
        output_filename = filename.replace(".csv", ".png")
        save_path = os.path.join(graphs_folder, output_filename)

        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close()

        print(f"Oluşturuldu: {output_filename}")

    except Exception as e:
        print(f"{filepath} işlenirken hata oldu: {e}")

print("Bitti!")