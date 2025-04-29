GentooIMGR Configuration Specification
======================================


---------------
Getting Started
---------------

If you want your own customized gentoo image, simply copy the gentooimgr/configs/base.json.example file:

```sh
cp gentooimgr/configs/base.json.example gentooimgr/myconfig.json
# modify your config file. It needs to be saved in the directory directly above or within gentooimgr to be
# included in the generated iso file and therefore mounted automatically; otherwise, copy it to the live image
python -m gentooimgr -c gentooimgr/myconfig.json install
```

