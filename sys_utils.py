"""
Copyright (C) 2019-2023 Abraham Smith

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import time
import os
from multiprocessing import Pool

def multi_process(func, repeat_args, fnames, chunk_size=None,
                  progress_hook=None, cpus=os.cpu_count()):
    """
    Use multiprocess pool to exec func.
    repeat args are used every time.
    A different f in fnames will be passed on
    each execution of func
    """
    print('calling', func.__name__, 'on', len(fnames), 'images')
    start = time.time()

    if chunk_size is None:
        chunk_size = len(fnames)

    results = []

    for i in range(0, len(fnames), chunk_size):
        pool = Pool(cpus)
        async_results = []
        chunk = fnames[i:i+chunk_size]
        for fname in chunk:
            res = pool.apply_async(func, args=list(repeat_args) + [fname])
            async_results.append(res)
        pool.close()
        pool.join()
        for res in async_results:
            results.append(res.get())
        if progress_hook is not None:
            progress_hook(i)
    print(func.__name__, 'on', len(fnames), 'images took', time.time() - start)
    return results
