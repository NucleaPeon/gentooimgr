import json
import gentooimgr.config
import gentooimgr.configs

def print_template(args, configjson):
    print(f"""------------------------ STATUS ------------------------

CPU_THREADS = {args.threads or 1}
TEMPORARY_DIRECTORY = {args.temporary_dir}
PROFILE = {args.profile}
""")
    print(f"CONFIG {args.config}")
    print(json.dumps(configjson, sort_keys=True, indent=4))

    inherit = configjson.get("inherit")
    if inherit:
        print(f"CONFIG {inherit}")
        j = gentooimgr.config.load_default_config(inherit)
        if not j:
            j = gentooimgr.config.load_config(inherit)

        print(json.dumps(j, sort_keys=True, indent=4))

    # print(f"""------------------------ PACKAGES ------------------------""")
    # for k, v in configjson.get("packages").items():
    #     print(k.upper())
    #     print("\t" + '\n\t'.join(v))
    #     print()
