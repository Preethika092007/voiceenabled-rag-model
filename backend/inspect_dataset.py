import json
import sys
try:
    from datasets import load_dataset_builder, get_dataset_config_names
    
    dataset_name = "ai4bharat/MSMARCO-XI"
    configs = get_dataset_config_names(dataset_name)
    print(f"Configs: {configs}")
    
    # Just take the first config for a quick inspect
    if configs:
        config = configs[0]
        builder = load_dataset_builder(dataset_name, config)
        print(f"Features for {config}: {builder.info.features}")
        
except Exception as e:
    print(f"Error: {e}")
