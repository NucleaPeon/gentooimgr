import json
import gentooimgr.config
import gentooimgr.configs

def print_template(configjson, **kwargs):
    print(f"""------------------------ STATUS ------------------------

CPU_THREADS = {kwargs.get("threads", 1)}
TEMPORARY_DIRECTORY = {kwargs.get("temporary_dir")}
PROFILE = {kwargs.get("profile") or "openrc"}
""")
    print(f"CONFIG {kwargs.get('config')}")
    print(json.dumps(configjson, sort_keys=True, indent=4))

    inherit = configjson.get("inherit")
    if inherit:
        print(f"CONFIG {inherit}")
        j = gentooimgr.config.load_default_config(inherit)
        if not j:
            j = gentooimgr.config.load_config(inherit)

        print(json.dumps(j, sort_keys=True, indent=4))
