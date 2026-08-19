const form =
    document.getElementById(
        "resumeForm"
    );


const input =
    document.getElementById(
        "resumeInput"
    );


const dropZone =
    document.getElementById(
        "dropZone"
    );


const selectedFile =
    document.getElementById(
        "selectedFile"
    );


const jobDescription =
    document.getElementById(
        "jobDescription"
    );


const analyzeButton =
    document.getElementById(
        "analyzeButton"
    );


const statusBox =
    document.getElementById(
        "status"
    );


const results =
    document.getElementById(
        "results"
    );



const categoryMax = {

    "Contact Information": 10,

    "Resume Structure": 20,

    "Skills and Job Relevance": 25,

    "Experience Impact": 20,

    "Education": 10,

    "ATS Readability": 15

};



input.addEventListener(
    "change",
    () => {

        selectedFile.textContent =
            input.files[0]?.name
            || "No file selected";

    }
);



[
    "dragenter",
    "dragover"
].forEach(name => {

    dropZone.addEventListener(
        name,
        event => {

            event.preventDefault();

            dropZone.classList.add(
                "dragging"
            );

        }
    );

});



[
    "dragleave",
    "drop"
].forEach(name => {

    dropZone.addEventListener(
        name,
        event => {

            event.preventDefault();

            dropZone.classList.remove(
                "dragging"
            );

        }
    );

});



dropZone.addEventListener(
    "drop",
    event => {

        if (
            event.dataTransfer.files.length
        ) {

            input.files =
                event.dataTransfer.files;


            selectedFile.textContent =
                event.dataTransfer
                    .files[0]
                    .name;

        }

    }
);



form.addEventListener(
    "submit",
    async event => {

        event.preventDefault();


        if (!input.files.length) {

            showStatus(
                "Choose a resume first."
            );

            return;

        }


        analyzeButton.disabled =
            true;


        analyzeButton.textContent =
            "Analyzing...";


        showStatus(
            "Reading and evaluating your resume..."
        );


        results.classList.add(
            "hidden"
        );


        const data =
            new FormData();


        data.append(
            "resume",
            input.files[0]
        );


        data.append(
            "job_description",
            jobDescription.value
        );


        try {


            const response =
                await fetch(
                    "/api/parse-resume",
                    {
                        method: "POST",
                        body: data
                    }
                );


            const result =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    result.error
                    || "Something went wrong."
                );

            }


            sessionStorage.setItem(
                "extractedResumeText",
                result.extracted_text || ""
            );


            sessionStorage.setItem(
                "resumeFilename",
                result.filename
                || input.files[0].name
            );


            renderResults(
                result
            );


            statusBox.classList.add(
                "hidden"
            );


        }

        catch (error) {


            showStatus(
                error.message
            );


        }

        finally {


            analyzeButton.disabled =
                false;


            analyzeButton.textContent =
                "Analyze Resume";


        }

    }
);



function showStatus(message) {

    statusBox.textContent =
        message;


    statusBox.classList.remove(
        "hidden"
    );

}



function safe(value) {

    return value || "—";

}



function renderChips(
    id,
    items,
    empty
) {

    const container =
        document.getElementById(id);


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (
        !items
        || !items.length
    ) {

        const span =
            document.createElement(
                "span"
            );


        span.className =
            "selected-file";


        span.textContent =
            empty;


        container.appendChild(
            span
        );


        return;

    }


    items.forEach(item => {


        const span =
            document.createElement(
                "span"
            );


        span.className =
            "chip";


        span.textContent =
            item;


        container.appendChild(
            span
        );


    });

}



function renderList(
    id,
    items
) {

    const list =
        document.getElementById(id);


    list.innerHTML = "";


    (
        items?.length
        ? items
        : ["No information available."]
    ).forEach(item => {


        const li =
            document.createElement(
                "li"
            );


        li.textContent =
            item;


        list.appendChild(
            li
        );


    });

}



function renderCategories(scores) {

    const container =
        document.getElementById(
            "categories"
        );


    container.innerHTML = "";


    Object.entries(
        scores || {}
    ).forEach(
        ([name, score]) => {


            const max =
                categoryMax[name]
                || 100;


            const percentage =
                Math.min(
                    100,
                    Math.round(
                        score
                        / max
                        * 100
                    )
                );


            const row =
                document.createElement(
                    "div"
                );


            row.className =
                "category";


            row.innerHTML = `

                <div class="category-top">

                    <strong>
                        ${name}
                    </strong>

                    <span>
                        ${score}/${max}
                    </span>

                </div>


                <div class="bar">

                    <span
                        style="width:${percentage}%"
                    ></span>

                </div>

            `;


            container.appendChild(
                row
            );


        }
    );

}



function renderSections(sections) {


    const found =
        Object.entries(
            sections || {}
        )

        .filter(
            ([, present]) =>
                present
        )

        .map(
            ([name]) =>
                name
        );


    renderChips(
        "sectionsFound",
        found,
        "No standard resume sections were confidently detected."
    );

}



function renderJobMatch(match) {


    const panel =
        document.getElementById(
            "jobMatchPanel"
        );


    if (
        !match
        || match.match_percentage === null
    ) {


        panel.classList.add(
            "hidden"
        );


        return;


    }


    document.getElementById(
        "matchPercentage"
    ).textContent =
        `${match.match_percentage}%`;


    renderChips(
        "matchedKeywords",
        match.matched_keywords,
        "No matching keywords were detected."
    );


    renderChips(
        "missingKeywords",
        match.missing_keywords,
        "No important missing keywords were detected."
    );


    panel.classList.remove(
        "hidden"
    );

}



function renderResults(data) {


    [
        "score",
        "ringScore"
    ].forEach(id => {


        document.getElementById(
            id
        ).textContent =
            data.score ?? 0;


    });


    document.getElementById(
        "rating"
    ).textContent =
        safe(data.rating);


    document.getElementById(
        "name"
    ).textContent =
        safe(data.name);


    document.getElementById(
        "email"
    ).textContent =
        safe(data.email);


    document.getElementById(
        "phone"
    ).textContent =
        safe(data.phone);




    document.getElementById(
        "wordCount"
    ).textContent =
        data.word_count ?? "—";


    document.getElementById(
        "bulletCount"
    ).textContent =
        data.bullet_count ?? "—";


    document.getElementById(
        "summary"
    ).textContent =
        safe(data.summary);


    renderChips(
        "skills",
        data.skills,
        "No skills matched the current skill dictionary."
    );


    renderSections(
        data.sections_found
    );


    renderList(
        "strengths",
        data.strengths
    );


    renderList(
        "improvements",
        data.improvements
    );


    renderCategories(
        data.category_scores
    );


    renderJobMatch(
        data.job_match
    );


    results.classList.remove(
        "hidden"
    );


    results.scrollIntoView({

        behavior: "smooth",

        block: "start"

    });

}