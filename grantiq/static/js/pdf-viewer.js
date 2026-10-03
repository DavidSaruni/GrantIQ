function initGrantPdfViewer(root) {
    var url = root.getAttribute("data-pdf-url");
    var workerSrc = root.getAttribute("data-pdf-worker");
    var pagesEl = root.querySelector(".grant-pdf-pages");
    var statusEl = root.querySelector(".grant-pdf-status");
    var pageInput = root.querySelector(".pdf-page-num");
    var pageCountEl = root.querySelector(".pdf-page-count");
    var zoomLabel = root.querySelector(".pdf-zoom-label");
    var pdfDoc = null;
    var currentScale = 1.15;
    var rendering = false;

    function setStatus(text) {
        if (!statusEl) {
            return;
        }
        statusEl.textContent = text || "";
        statusEl.style.display = text ? "block" : "none";
    }

    if (!url || !pagesEl) {
        return;
    }
    if (typeof pdfjsLib === "undefined") {
        setStatus("PDF viewer failed to load. Use Download to open the document.");
        return;
    }

    if (workerSrc) {
        pdfjsLib.GlobalWorkerOptions.workerSrc = workerSrc;
    }

    function fitScale(page) {
        var width = pagesEl.clientWidth - 32;
        if (width < 200) {
            width = 700;
        }
        var base = page.getViewport({ scale: 1 }).width;
        return Math.max(0.6, Math.min(2.2, width / base));
    }

    function renderAll() {
        if (!pdfDoc || rendering) {
            return Promise.resolve();
        }
        rendering = true;
        pagesEl.innerHTML = "";
        var chain = Promise.resolve();
        var i;
        for (i = 1; i <= pdfDoc.numPages; i += 1) {
            (function (pageNum) {
                chain = chain.then(function () {
                    return pdfDoc.getPage(pageNum).then(function (page) {
                        var viewport = page.getViewport({ scale: currentScale });
                        var canvas = document.createElement("canvas");
                        var context = canvas.getContext("2d");
                        canvas.width = viewport.width;
                        canvas.height = viewport.height;
                        canvas.className = "grant-pdf-page";
                        canvas.setAttribute("data-page", String(pageNum));
                        pagesEl.appendChild(canvas);
                        return page.render({
                            canvasContext: context,
                            viewport: viewport,
                        }).promise;
                    });
                });
            })(i);
        }
        return chain.then(function () {
            rendering = false;
            if (zoomLabel) {
                zoomLabel.textContent = Math.round(currentScale * 100) + "%";
            }
        }).catch(function () {
            rendering = false;
            setStatus("Could not render this PDF. Use Download to open it.");
        });
    }

    function openPdf(data) {
        return pdfjsLib.getDocument({ data: data }).promise.catch(function () {
            return pdfjsLib.getDocument({ data: data, disableWorker: true }).promise;
        });
    }

    setStatus("Loading document…");
    fetch(url, { credentials: "same-origin" })
        .then(function (res) {
            if (!res.ok) {
                throw new Error("HTTP " + res.status);
            }
            return res.arrayBuffer();
        })
        .then(function (data) {
            if (!data || data.byteLength < 5) {
                throw new Error("empty file");
            }
            return openPdf(data);
        })
        .then(function (pdf) {
            pdfDoc = pdf;
            if (pageCountEl) {
                pageCountEl.textContent = String(pdf.numPages);
            }
            if (pageInput) {
                pageInput.value = "1";
                pageInput.max = String(pdf.numPages);
            }
            setStatus("");
            return pdf.getPage(1).then(function (page) {
                currentScale = fitScale(page);
                return renderAll();
            });
        })
        .catch(function () {
            setStatus("Could not load this PDF. Use Download to open it.");
        });

    var prevBtn = root.querySelector(".pdf-prev");
    var nextBtn = root.querySelector(".pdf-next");
    var zoomInBtn = root.querySelector(".pdf-zoom-in");
    var zoomOutBtn = root.querySelector(".pdf-zoom-out");

    function goToPage(num) {
        var pageEl = pagesEl.querySelector('[data-page="' + num + '"]');
        if (pageEl) {
            pageEl.scrollIntoView({ block: "start", behavior: "smooth" });
        }
        if (pageInput) {
            pageInput.value = String(num);
        }
    }

    if (prevBtn) {
        prevBtn.addEventListener("click", function () {
            var current = parseInt(pageInput.value, 10) || 1;
            goToPage(Math.max(1, current - 1));
        });
    }
    if (nextBtn) {
        nextBtn.addEventListener("click", function () {
            var current = parseInt(pageInput.value, 10) || 1;
            var max = pdfDoc ? pdfDoc.numPages : 1;
            goToPage(Math.min(max, current + 1));
        });
    }
    if (pageInput) {
        pageInput.addEventListener("change", function () {
            var num = parseInt(pageInput.value, 10) || 1;
            var max = pdfDoc ? pdfDoc.numPages : 1;
            goToPage(Math.min(max, Math.max(1, num)));
        });
    }
    if (zoomInBtn) {
        zoomInBtn.addEventListener("click", function () {
            currentScale = Math.min(2.4, currentScale + 0.15);
            renderAll();
        });
    }
    if (zoomOutBtn) {
        zoomOutBtn.addEventListener("click", function () {
            currentScale = Math.max(0.5, currentScale - 0.15);
            renderAll();
        });
    }

    pagesEl.addEventListener("scroll", function () {
        var canvases = pagesEl.querySelectorAll(".grant-pdf-page");
        var area = pagesEl.getBoundingClientRect();
        var found = 1;
        canvases.forEach(function (canvas) {
            var top = canvas.getBoundingClientRect().top - area.top;
            if (top <= 48) {
                found = parseInt(canvas.getAttribute("data-page"), 10);
            }
        });
        if (pageInput) {
            pageInput.value = String(found);
        }
    });
}

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-pdf-url]").forEach(initGrantPdfViewer);
});
