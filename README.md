# Distributed Task Scheduler

A real-time preemptive priority-based task scheduler developed in Python for the Operating Systems course. This project simulates core scheduling algorithms, resource constraints (CPU, RAM, Space), and concurrency control using multithreading.

## Key Features

- Preemptive Priority Scheduling (higher priority tasks preempt running tasks)
- Dynamic Resource Allocation (tracks CPU, RAM, and Space availability)
- Min-Heap Ready Queue (manages waiting tasks efficiently)
- Terminal Interface (interactive CLI with active state visualization)
- Thread-Safe Design (utilizes Python locks for concurrent task execution)

## System Limits

- Total CPU: 100 units
- Total RAM: 512 MB
- Total Space: 2000 MB

## How to Run

1. Clone the repository:
   git clone https://github.com/md-ibna-labid/Distributed-Task-Scheduler.git

2. Navigate to the folder:
   cd Distributed-Task-Scheduler

3. Execute the Python script:
   python main.py

## Available Commands

Once running, use these commands in the terminal:

- add <task_id> <priority> <cpu> <ram> <space> <duration>
  Example: add T1 1 20 128 500 10
- refresh
- quit

## Project Structure

- main.py: Main source code for the task scheduler
- DTS Project Report.pdf: Detailed project documentation
- README.md: Setup instructions and project overview

## Authors

- Md. Ibna Labid
- Fahim Montasir