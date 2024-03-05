from cx_Freeze import setup, Executable

setup(

       name="Annotator3",

       version="1.0",

       description="OneAI Annotator for RequiresRewrite",

       executables=[Executable("main_program.py")],

)   