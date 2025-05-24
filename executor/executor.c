// executor.c

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <unistd.h>
#include <sys/wait.h>
#include <json-c/json.h>

#define SHM_KEY 1234
#define SHM_SIZE 4096
#define MAX_ARGS 100

void execute_command(struct json_object *cmd_array) {
    if (!cmd_array || json_object_get_type(cmd_array) != json_type_array) {
        fprintf(stderr, "Invalid command array\n");
        return;
    }

    int len = json_object_array_length(cmd_array);
    if (len > MAX_ARGS) {
        fprintf(stderr, "Too many arguments\n");
        return;
    }

    char *args[MAX_ARGS + 1];
    for (int i = 0; i < len; i++) {
        struct json_object *arg_obj = json_object_array_get_idx(cmd_array, i);
        if (!arg_obj || json_object_get_type(arg_obj) != json_type_string) {
            fprintf(stderr, "Invalid argument type at index %d\n", i);
            return;
        }
        args[i] = (char *)json_object_get_string(arg_obj);
    }
    args[len] = NULL;

    pid_t pid = fork();
    if (pid == 0) {
        // Child process
        execvp(args[0], args);
        perror("execvp failed");
        exit(1);
    } else if (pid > 0) {
        // Parent process
        wait(NULL);
    } else {
        perror("fork failed");
    }
}

int main() {
    int shmid = shmget(SHM_KEY, SHM_SIZE, 0666);
    if (shmid == -1) {
        perror("shmget failed");
        return 1;
    }

    char *data = (char *)shmat(shmid, NULL, 0);
    if (data == (char *)-1) {
        perror("shmat failed");
        return 1;
    }

    struct json_object *parsed = json_tokener_parse(data);
    if (!parsed) {
        fprintf(stderr, "Failed to parse JSON from shared memory\n");
        shmdt(data);
        return 1;
    }

    if (json_object_get_type(parsed) == json_type_array) {
        struct json_object *first = json_object_array_get_idx(parsed, 0);
        if (first && json_object_get_type(first) == json_type_array) {
            // Nested array (multiple commands)
            for (int i = 0; i < json_object_array_length(parsed); i++) {
                struct json_object *cmd = json_object_array_get_idx(parsed, i);
                execute_command(cmd);
            }
        } else {
            // Single command array
            execute_command(parsed);
        }
    } else if (json_object_get_type(parsed) == json_type_string) {
        printf("LLM Response: %s\n", json_object_get_string(parsed));
    } else {
        fprintf(stderr, "Unexpected JSON format from shared memory.\n");
    }

    shmdt(data);
    return 0;
}
