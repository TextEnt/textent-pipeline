""" This is a sample script for using RTK (Release the krakens)

It takes a file with a list of manifests to download from IIIF (See manifests.txt) and passes it in a suit of commands:

0. It downloads manifests and transform them into CSV files
1. It downloads images from the manifests
2. It applies YALTAi segmentation with line segmentation
3. It fixes up the image PATH of XML files
4. It processes the text as well through Kraken
5. It removes the image files (from the one hunder object that were meant to be done in group)

The batch file should be lower if you want to keep the space used low, specifically if you use DownloadIIIFManifest.

"""
from rtk.task import KrakenAltoCleanUpCommand, YALTAiCommand, KrakenRecognizerCommand, ExtractZoneAltoCommand
from rtk import utils
import glob
from sys import argv
import time

start = time.time()

folders = glob.glob("images/*")

if len(argv) == 2:
    num_workers = int(argv[1])
else:
    num_workers = 5

for i in range(0, len(folders), 4):
    batch = [
        file
        for folder in folders[i:i+4]
        for file in glob.glob(f"{folder}/*.png")
    ]
    startYalt = time.time()
    # Apply YALTAi
    print("[Task] Segment, size of batch ", len(batch))
    yaltai = YALTAiCommand(
        batch,
        binary="env/bin/yaltai",
        device="cuda:0",
        yolo_model="models/ladas-1280-l.pt",
        verbose=True,
        raise_on_error=False,
        allow_failure=False,
        multiprocess=30,  # GPU Memory // 5gb
        check_content=False,
        line_model = "models/blla.mlmodel"
    )
    yaltai.process()
    endYalt = time.time()
    print("[Time] Yaltai: ", endYalt - startYalt)
    print("Yaltai output files len ", len(yaltai.output_files))

    # Clean-up the relative filepath of Kraken Serialization
    print("[Task] Clean-Up Serialization")
    cleanup = KrakenAltoCleanUpCommand(yaltai.output_files)
    cleanup.process()

    startKrak = time.time()
    # Apply Kraken
    print("[Task] OCR")
    kraken = KrakenRecognizerCommand(
        yaltai.output_files,
        binary="env/bin/kraken",
        #binary="yaltaienv/bin/kraken",
        device="cuda:0",
        model="models/catmus-print-fondue-large.mlmodel",
        multiprocess=30,  # GPU Memory // 3gb
        check_content=True  # Required ?
    )
    kraken.process()
    endKrak = time.time()
    print("[Time] Kraken: ", endKrak - startKrak)

end = time.time()
print("[Time] total: ", end - start)
