import ZipFile
import Downloads: download
import DataStructures: DefaultDict
import SimulationService.Service.Execution.Interface.Available: simulate, calibrate_then_simulate
import SimulationService.Service.Execution.Interface.ProblemInputs: coerce_model

owner = "DARPA-ASKEM"
repo = "experiments"
revision = "953808422c72dd0ab91dc7114ff3e581dfef0dac" 
biomodels_path = "/thin-thread-examples/mira_v2/biomodels"
model_filehandle = "model_askenet.json"
model_file = biomodels_path * r"/(.+)/" * model_filehandle 

biomodels_zip = ZipFile.Reader(download("https://github.com/$owner/$repo/archive/$revision.zip"))
biomodels = [match(model_file, file.name).captures[1] => (String ∘ read)(file) for file in biomodels_zip.files if !(isnothing ∘ match)(model_file, file.name)] 

status = DefaultDict{String, Dict{String, Bool}}(() -> Dict{String, Bool}())
for (name, biomodel) in biomodels
    print("$name : ")
    try
        coerce_model(biomodel)
        status[name]["coerce"] = true
        print("COERCES")
        try
            biomodel = simulate(coerce_model(biomodel), (0.0, 100.0), nothing)
            status[name]["simulate"] = true
            println("; SIMULATES")
        catch e
            status[name]["simulate"] = false
            println(";")
        end
    catch e
        status[name]["coerce"] = false
        status[name]["simulate"] = false
        println(";")
    end
end
