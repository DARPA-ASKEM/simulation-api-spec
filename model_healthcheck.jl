import ZipFile
import Downloads: download
import SimulationService.Service.Execution.Interface.ProblemInputs: coerce_model
import SimulationService.Service.Execution.Interface.Available: simulate

owner = "DARPA-ASKEM"
repo = "experiments"
revision = "953808422c72dd0ab91dc7114ff3e581dfef0dac" 
biomodels_path = "/thin-thread-examples/mira_v2/biomodels"
model_filehandle = "model_askenet.json"
model_file = biomodels_path * r"/(.+)/" * model_filehandle 

struct Status
    success::Bool
    reason::String
    Status(success::Bool=false, reason::String="") = new(success, reason)
end

mutable struct ReportEntry
    name::String
    coerce::Status
    simulate::Status
    ReportEntry(name, coerce::Status=Status(), simulate::Status=Status()) = new(string(name), coerce, simulate)
end

function generate_report()
    biomodels_zip = ZipFile.Reader(download("https://github.com/$owner/$repo/archive/$revision.zip"))
    biomodels = [match(model_file, file.name).captures[1] => (String ∘ read)(file) for file in biomodels_zip.files if !(isnothing ∘ match)(model_file, file.name)] 

    report = ReportEntry[]

    for (name, biomodel) in biomodels
        push!(report, ReportEntry(name))
        try
            coerce_model(biomodel)
            report[end].coerce = Status(true, "")
        catch e
            report[end].coerce = Status(false, string(e))
        else
            try
                simulate(coerce_model(biomodel), (0.0, 100.0), nothing)
                report[end].simulate = Status(true, nothing)
            catch e
                report[end].simulate = Status(false, string(e))
            end
        end
    end
    return report
end

function print_report!(report::Array{ReportEntry} = generate_report())
    for entry in report
        line = string(entry.name) * ":\t"
        if entry.coerce.success
            line *= "COERCES\t" 
        else
            line *= "[error: $(entry.coerce.reason)];" 
            println(line)
            continue
        end
        if entry.simulate.success
            line *= "SIMULATES\t" 
        else
            line *= "[error: $(entry.simulate.reason)];" 
            println(line)
        end
    end
end
