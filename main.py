#!/usr/bin/env python3
import time
import threading
import os
import heapq

# ================================
# SYSTEM CONFIG
# ================================
TOTAL_CPU = 100
TOTAL_RAM = 512
TOTAL_SPACE = 2000

# ================================
# GLOBAL STATE
# ================================
avail_cpu = TOTAL_CPU
avail_ram = TOTAL_RAM
avail_space = TOTAL_SPACE

running = []              # always sorted: only running[0] is ACTIVE
ready = []                # heap: (priority, remaining, counter, task)
counter = 0

lock = threading.Lock()
terminate = False

# ================================
# COLORS
# ================================
CYAN = "\033[1;36m"
BLUE = "\033[1;34m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
MAGENTA = "\033[1;35m"
BOLD = "\033[1m"
RESET = "\033[0m"

# ================================
# DRAW UI
# ================================
def draw():
    os.system("cls" if os.name == "nt" else "clear")

    # ASCII Art Title
    title = f"""
{CYAN}╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     {BOLD}DISTRIBUTED TASK SCHEDULER{RESET}{CYAN}                      ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝{RESET}
"""
    print(title)

    with lock:
        print(f"{BLUE}SYSTEM STATUS{RESET}")
        print(f"  {GREEN}TOTAL{RESET}      CPU={TOTAL_CPU:<3}  RAM={TOTAL_RAM:<3}MB  SPACE={TOTAL_SPACE}MB")
        print(f"  {YELLOW}AVAILABLE{RESET}  CPU={avail_cpu:<3}  RAM={avail_ram:<3}MB  SPACE={avail_space}MB\n")

        print(f"{BLUE}RUNNING TASKS{RESET}")
        if not running:
            print("  (none)")
        else:
            print(f"  {'TASK':<6} {'PR':<3} {'CPU':<4} {'RAM':<4} {'SPACE':<7} {'REMAIN(s)':<11} STATUS")
            for t in running:
                status = f"{GREEN}ACTIVE{RESET}" if t["active"] else f"{YELLOW}PAUSED{RESET}"
                print(f"  {t['id']:<6} {t['pr']:<3} {t['cpu']:<4} {t['ram']:<4} {t['space']:<7} "
                      f"{int(t['remaining']):<11} {status}")

        print(f"\n{BLUE}READY QUEUE{RESET}")
        if not ready:
            print("  (empty)")
        else:
            print(f"  {'TASK':<6} {'PR':<3} {'CPU':<4} {'RAM':<4} {'SPACE':<7} {'DUR':<6}")
            for pr, rem, _, t in sorted(ready):
                print(f"  {t['id']:<6} {pr:<3} {t['cpu']:<4} {t['ram']:<4} {t['space']:<7} {int(rem):<6}")

    print(f"\n{MAGENTA}Commands:{RESET}")
    print("  add <id> <priority> <cpu> <ram> <space> <duration>")
    print("  refresh")
    print("  quit\n")

# ================================
# HELPERS
# ================================
def enough_resource(t):
    return (
        t["cpu"] <= avail_cpu and
        t["ram"] <= avail_ram and
        t["space"] <= avail_space
    )

def pause_task(t):
    t["active"] = False

def activate_task(t):
    t["active"] = True
    t["last_tick"] = time.time()

# ================================
# INSERT TASK (Option A)
# Sort by priority ASC then remaining ASC
# ================================
def insert_running(task):
    # Don't allocate resources here - they should already be allocated
    task["active"] = False
    running.append(task)
    running.sort(key=lambda x: (x["pr"], x["remaining"]))

    # ensure ONLY first task is active
    for i, t in enumerate(running):
        if i == 0:
            activate_task(t)
        else:
            t["active"] = False

# ================================
# PREEMPTION + NEW TASK HANDLING
# ================================
def schedule_new_task(task):
    global avail_cpu, avail_ram, avail_space, counter

    # CASE 1 — no running task
    if not running:
        if enough_resource(task):
            avail_cpu -= task["cpu"]
            avail_ram -= task["ram"]
            avail_space -= task["space"]
            insert_running(task)
        else:
            heapq.heappush(ready, (task["pr"], task["remaining"], counter, task))
            counter += 1
        return

    top = running[0]

    # PREEMPTION RULE (Option A)
    preempt = (
        task["pr"] < top["pr"] or
        (task["pr"] == top["pr"] and task["remaining"] < top["remaining"])
    )

    if preempt:
        # Check if we have enough resources for the new task
        if not enough_resource(task):
            # Can't preempt - queue the new task
            heapq.heappush(ready, (task["pr"], task["remaining"], counter, task))
            counter += 1
            return
        
        # Pause top task but DON'T free its resources
        # (resources stay allocated to paused tasks)
        pause_task(top)
        
        # Allocate resources for new task
        avail_cpu -= task["cpu"]
        avail_ram -= task["ram"]
        avail_space -= task["space"]

        # Remove the old top from running list before re-inserting
        running.remove(top)
        
        # Insert new task
        insert_running(task)
        
        # Reinsert paused task into running list (properly sorted)
        running.append(top)
        running.sort(key=lambda x: (x["pr"], x["remaining"]))

        # reapply ACTIVE/PAUSED flags
        for i, t in enumerate(running):
            if i == 0:
                activate_task(t)
            else:
                t["active"] = False

        return

    # No preemption — try to start normally
    if enough_resource(task):
        avail_cpu -= task["cpu"]
        avail_ram -= task["ram"]
        avail_space -= task["space"]
        insert_running(task)
        return

    # Otherwise queue
    heapq.heappush(ready, (task["pr"], task["remaining"], counter, task))
    counter += 1

# ================================
# START READY QUEUE IF RESOURCES AVAILABLE
# ================================
def try_start_ready():
    global avail_cpu, avail_ram, avail_space

    changed = True
    while ready and changed:
        changed = False
        pr, rem, _, t = ready[0]

        if enough_resource(t):
            heapq.heappop(ready)
            avail_cpu -= t["cpu"]
            avail_ram -= t["ram"]
            avail_space -= t["space"]
            insert_running(t)
            changed = True

# ================================
# BACKGROUND TICK
# ================================
def tick():
    global avail_cpu, avail_ram, avail_space, terminate

    while not terminate:
        time.sleep(1)

        with lock:
            if not running:
                continue

            active = running[0]
            
            # Only tick if the task is actually active
            if not active.get("active", False):
                continue

            now = time.time()
            elapsed = now - active.get("last_tick", now)
            active["remaining"] -= elapsed
            active["last_tick"] = now

            if active["remaining"] <= 0:
                # Free resources only for the completed task
                avail_cpu += active["cpu"]
                avail_ram += active["ram"]
                avail_space += active["space"]

                running.pop(0)
                
                # If there are more tasks in running, activate the next one
                if running:
                    next_task = running[0]
                    # Check if next task has enough resources (it should, since it was paused)
                    # But we need to make sure resources were already allocated
                    if not next_task.get("active", False):
                        activate_task(next_task)
                
                # Try to start tasks from ready queue
                try_start_ready()

# ================================
# MAIN LOOP
# ================================
def main():
    global terminate
    draw()

    while True:
        cmd = input("> ").split()

        if not cmd:
            continue

        if cmd[0] == "quit":
            terminate = True
            time.sleep(0.2)
            break

        if cmd[0] == "refresh":
            draw()
            continue

        if cmd[0] == "add":
            if len(cmd) != 7:
                print("Usage: add <id> <priority> <cpu> <ram> <space> <duration>")
                continue

            _, tid, pr, cpu, ram, space, dur = cmd
            pr, cpu, ram, space, dur = map(int, [pr, cpu, ram, space, dur])

            task = {
                "id": tid,
                "pr": pr,
                "cpu": cpu,
                "ram": ram,
                "space": space,
                "remaining": float(dur),
                "active": False,
                "last_tick": None
            }

            with lock:
                schedule_new_task(task)
            
            draw()
            continue

        print("Unknown command")


# ================================
# START
# ================================
if __name__ == "__main__":
    threading.Thread(target=tick, daemon=True).start()
    main()