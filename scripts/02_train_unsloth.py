from unsloth import FastLanguageModel
import torch
from trl import SFTTrainer
from transformers import TrainingArguments
from datasets import load_dataset
import os

# Paths (Updated for easy use on Cloud Server)
TRAIN_DATA = "train.jsonl"
VAL_DATA = "val.jsonl"
OUTPUT_DIR = "unsloth_medgemma_v2"


# Unsloth Settings
max_seq_length = 2048
dtype = None # Auto detect
load_in_4bit = True # 4-bit quantization (QLoRA)

# Load Model
model_id = "google/medgemma-1.5-4b-it" 
# Note: If this model is not public on HF, ensure you are logged in using `huggingface-cli login`
# If you actually meant a standard Gemma model, use "unsloth/gemma-1.5-2b-it" or similar.

print(f"Loading Base Model: {model_id}...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = model_id,
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)

# Configure PEFT / LoRA
print("Configuring LoRA Adapters...")
model = FastLanguageModel.get_peft_model(
    model,
    r = 16, # Rank
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj",],
    lora_alpha = 16,
    lora_dropout = 0, # Unsloth optimizes this to 0
    bias = "none",
    use_gradient_checkpointing = "unsloth",
    random_state = 42,
    use_rslora = False,
    loftq_config = None,
)

# Load Dataset
print("Loading JSONL Datasets...")
train_dataset = load_dataset("json", data_files=TRAIN_DATA, split="train")
val_dataset = load_dataset("json", data_files=VAL_DATA, split="train")

# ChatML Formatting Function for Unsloth
from unsloth.chat_templates import get_chat_template
tokenizer = get_chat_template(
    tokenizer,
    chat_template = "chatml",
    mapping = {"role": "role", "content": "content", "user": "user", "assistant": "assistant"}, 
)

def formatting_prompts_func(examples):
    conversations = examples["messages"]
    texts = [tokenizer.apply_chat_template(convo, tokenize = False, add_generation_prompt = False) for convo in conversations]
    return { "text" : texts, }

print("Formatting templates...")
train_dataset = train_dataset.map(formatting_prompts_func, batched = True)
val_dataset = val_dataset.map(formatting_prompts_func, batched = True)

# Trainer
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = train_dataset,
    eval_dataset = val_dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    dataset_num_proc = 2,
    packing = False, # Can make training 5x faster for short sequences
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 10,
        num_train_epochs = 5,
        learning_rate = 2e-4,
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(),
        logging_steps = 10,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 42,
        output_dir = OUTPUT_DIR,
        
        # Validation & Checkpoint Strategy
        eval_strategy = "epoch",         # Evaluate Validation Loss at the end of every epoch
        save_strategy = "no",            # [FIX แก้บั๊ก] ปิดการเซฟระหว่างทางเพื่อแก้ปัญหา PicklingError ของ TRL
        # save_total_limit = 2,            
        # load_best_model_at_end = True,   
        # metric_for_best_model = "eval_loss",
    ),
)

# Train
print("Starting Training...")
trainer_stats = trainer.train()

# Save Model
print(f"Saving model to {OUTPUT_DIR}...")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print("Training Complete!")
