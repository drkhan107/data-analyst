# import json
# import docker
# import os
# from docker.errors import NotFound
 

# client = docker.from_env()

# def run_code_in_docker(session_id, code, files):
#     source_path="/home/asif-iqbal-khan/data/proj-001"
#     input_dir=source_path+"/input_files/"
#     output_dir=source_path+"/output_files/"

#     os.makedirs(output_dir, exist_ok=True)

#     container_name = f"sandbox_{session_id}"

#     # ---------------------------------
#     # GET OR CREATE CONTAINER
#     # ---------------------------------
#     try:
#         container = client.containers.get("my_container")

#         if container.status != "running":
#             container.start()

#         print("Reusing existing container")

#     except NotFound:
#         container = client.containers.run(
            
#             image="secure-python-sandbox",
#             name=container_name,
#             detach=True,

#             # network_mode="none",
#             # read_only=True,
#             mem_limit="512m",
#             cpu_period=100000,
#             cpu_quota=100000,
#             pids_limit=64,

#             mounts=[
#                 docker.types.Mount("/data", input_dir, "bind", read_only=True),
#                 docker.types.Mount("/output", output_dir, "bind", read_only=False),
#             ],

#             # command=["sleep", "infinity"],
#             command=["tail", "-f", "/dev/null"],
#         )
#         print("Created new container")
#     # container.reload()
#     # ---------------------------------
#     # EXECUTE CODE
#     # ---------------------------------

#     print("container started", container)
#     payload = {
#         "code": code,
#         "files": {
#             name: f"/data/{name}" for name in files
#         }
#     }

#     result = container.exec_run(
        
#         cmd=["python", "/sandbox/executor.py"],
#         stdin=True,
#         stdout=True,
#         stderr=True,
#         demux=True,
#     )

#     stdout, stderr = result.output

#     if stderr:
#         raise RuntimeError(stderr.decode())

#     return json.loads(stdout.decode())


import docker
import json
import os
from docker.errors import NotFound
def run_code_in_docker(payload):
    client = docker.from_env()

    python_code = payload["code"]
    df_csv = payload.get("df_csv") or None

    source_path=payload['source_path']
    input_dir=source_path+"/input_files/"
    output_dir=payload['output_path']

    docker_image=payload['docker_image']

    os.makedirs(output_dir, exist_ok=True)

    # Define environment variables
    env_vars = {
        "CODE": python_code,
        "PROJECT_ID": "sdk_project",
        "SESSION_ID": "sdk_session_1"
    }
    
    if df_csv:
        env_vars["DF_CSV"] = df_csv
    uid = os.getuid()
    gid = os.getgid()
    container_name=payload['project_id']
    try:


        # try:
        #     # Try to get existing container
        #     container = client.containers.get(container_name)
        #     print("Container exists, starting it...")
        #     container.start()

        # except NotFound:
        #     print("Container does not exist, creating it...")

        #     container = client.containers.create(
        #         image=docker_image,
        #         name=container_name,
        #         environment=env_vars,
        #         mem_limit="512m",
        #         cpu_period=100000,
        #         cpu_quota=100000,  # 1 CPU
        #         pids_limit=64,
        #         user=f"{uid}:{gid}",
        #         mounts=[
        #             docker.types.Mount("/data", input_dir, "bind", read_only=True),
        #             docker.types.Mount("/tmp", output_dir, "bind", read_only=False),
        #         ],
        #         # stderr=True,
        #         tty=False,
        #         detach=True,
        #     )
        #     print("Container created, starting it...")
        #     container.start()

        # # Optional: wait and get logs
        # exit_status = container.wait()
        # raw_logs = container.logs(stderr=True, stdout=True)



        raw_logs = client.containers.run(
            docker_image,
            environment=env_vars,
            # read_only=True,
            mem_limit="512m",
            cpu_period=100000,
            cpu_quota=100000,  # 1 CPU
            pids_limit=64,
            user=f"{uid}:{gid}",
            # tmpfs = ["/tmp:rw,noexec,nosuid,size=64m"],

            mounts=[
                docker.types.Mount("/data", input_dir, "bind", read_only=True),
                docker.types.Mount("/tmp", output_dir, "bind", read_only=False),
            ],

            remove=True,
            stderr=True # Capture stderr as well
        )
        
        # The SDK returns bytes, so we decode to string
        output_str = raw_logs.decode('utf-8').strip()
        # print("Output:", output_str)
        # In our main.py, we carefully printed ONLY the JSON to stdout.
        # However, if there are warnings mixed in, we might need to find the JSON.
        # This simple approach assumes the last line is the JSON.
        lines = output_str.split('\n')
        json_line = lines[-1] 

        response_data = json.loads(json_line)
        return response_data

    except docker.errors.ContainerError as e:
        print(f"Container failed: {e}")
        # e.stderr might contain the traceback
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

