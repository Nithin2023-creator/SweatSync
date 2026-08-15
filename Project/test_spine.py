import os
import sys
import asyncio

# Add the project root to sys.path
sys.path.append('/home/vitwit/Nithin/SweatSync-V2/SweatSync')

from sweatsync.exercise_fetcher import fetch_exercises_by_target

async def main():
    exercises = await asyncio.to_thread(fetch_exercises_by_target, "spine", limit=20)
    print(f"Spine: {len(exercises)}")
    print(exercises)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv('/home/vitwit/Nithin/SweatSync-V2/SweatSync/.env')
    asyncio.run(main())
