
def print_template(**kwargs):
    print(f"""------------------------ STATUS ------------------------

CPU_THREADS = {kwargs.get("threads", 1)}
TEMPORARY_DIRECTORY = {kwargs.get("temporary_dir")}
PROFILE = {kwargs.get("profile") or "openrc"}
""")
