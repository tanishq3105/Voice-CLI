import sysv_ipc
import json
import sys

def write_to_shm(commands):
    SHM_KEY = 1234
    SHM_SIZE = 4096

    try:
        memory = sysv_ipc.SharedMemory(SHM_KEY, sysv_ipc.IPC_CREAT, size=SHM_SIZE)
    except Exception as e:
        print(f"Error creating shared memory: {e}")
        sys.exit(1)

    data = json.dumps(commands)

    # Clear the shared memory area before writing
    memory.write(b'\0' * SHM_SIZE)
    memory.write(data.encode('utf-8'))

if __name__ == "__main__":
    try:
        with open("command_output.txt") as f:
            commands = json.load(f)
    except Exception as e:
        print(f"Error reading command_output.txt: {e}")
        sys.exit(1)

    write_to_shm(commands)
    print("Commands written to shared memory successfully.")
