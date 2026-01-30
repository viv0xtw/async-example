from time import perf_counter
import asyncio
from async_example import async_main
if __name__ == "__main__":
    start = perf_counter()
    asyncio.run(async_main())
    print(f"Task completed in: {perf_counter() - start:.2f}")