"""
Human Grading Interface
Run this after evaluation to manually grade the human test results
"""

import json
import os
from datetime import datetime


def load_tasks(file_path: str = "human_grading_tasks.json") -> dict:
    """Load pending tasks."""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        print("Run evaluation first to generate tasks.")
        return None
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def grade_tasks_interactive():
    """Interactive grading interface."""
    data = load_tasks()
    if not data:
        return
    
    tasks = data["tasks"]
    print("\n" + "=" * 70)
    print("👤 HUMAN GRADING INTERFACE")
    print("=" * 70)
    print(f"Total tasks to grade: {len(tasks)}")
    print("Enter score (0-5) for each task, or 'q' to quit and save progress")
    print("=" * 70)
    
    for i, task in enumerate(tasks, 1):
        if task.get("human_score") is not None:
            print(f"\n[{i}/{len(tasks)}] {task['test_id']} - Already graded: {task['human_score']}/5")
            continue
        
        print(f"\n{'=' * 70}")
        print(f"[{i}/{len(tasks)}] Test ID: {task['test_id']} | Agent: {task['agent'].upper()}")
        print("-" * 70)
        print(f"QUESTION: {task['question']}")
        print("-" * 70)
        print(f"ANSWER:\n{task['answer']}")
        print("-" * 70)
        print(f"RUBRIC:{task['rubric']}")
        print("-" * 70)
        
        while True:
            score_input = input("\nEnter score (0-5) or 'q' to quit: ").strip()
            
            if score_input.lower() == 'q':
                save_results(data)
                return
            
            try:
                score = float(score_input)
                if 0 <= score <= 5:
                    task["human_score"] = score
                    task["graded_at"] = datetime.now().isoformat()
                    
                    notes = input("Notes (optional, press Enter to skip): ").strip()
                    if notes:
                        task["human_notes"] = notes
                    
                    print(f"✅ Recorded: {score}/5")
                    break
                else:
                    print("❌ Score must be between 0 and 5")
            except ValueError:
                print("❌ Invalid input. Enter a number 0-5 or 'q'")
    
    save_results(data)
    print("\n✅ All tasks graded!")


def save_results(data: dict, output_file: str = "human_grading_results.json"):
    """Save grading results."""
    graded_count = sum(1 for t in data["tasks"] if t.get("human_score") is not None)
    
    data["graded_at"] = datetime.now().isoformat()
    data["graded_count"] = graded_count
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved {graded_count}/{len(data['tasks'])} graded tasks to: {output_file}")


def print_summary():
    """Print grading summary."""
    try:
        with open("human_grading_results.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ No results file found. Run grading first.")
        return
    
    tasks = data["tasks"]
    graded = [t for t in tasks if t.get("human_score") is not None]
    
    print("\n" + "=" * 50)
    print("📊 HUMAN GRADING SUMMARY")
    print("=" * 50)
    
    # Needle Agent
    needle_tasks = [t for t in graded if t["agent"] == "needle"]
    if needle_tasks:
        avg = sum(t["human_score"] for t in needle_tasks) / len(needle_tasks)
        passed = sum(1 for t in needle_tasks if t["human_score"] >= 3)
        print(f"\n🎯 Needle Agent ({len(needle_tasks)} graded):")
        print(f"   Average Score: {avg:.2f}/5.0")
        print(f"   Pass Rate: {passed}/{len(needle_tasks)} ({passed/len(needle_tasks)*100:.0f}%)")
    
    # Summary Agent
    summary_tasks = [t for t in graded if t["agent"] == "summary"]
    if summary_tasks:
        avg = sum(t["human_score"] for t in summary_tasks) / len(summary_tasks)
        passed = sum(1 for t in summary_tasks if t["human_score"] >= 3)
        print(f"\n📋 Summary Agent ({len(summary_tasks)} graded):")
        print(f"   Average Score: {avg:.2f}/5.0")
        print(f"   Pass Rate: {passed}/{len(summary_tasks)} ({passed/len(summary_tasks)*100:.0f}%)")
    
    # Overall
    if graded:
        overall_avg = sum(t["human_score"] for t in graded) / len(graded)
        print(f"\n{'=' * 50}")
        print(f"📈 Overall Human Grading: {overall_avg:.2f}/5.0")
    
    print("=" * 50)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        print_summary()
    else:
        grade_tasks_interactive()