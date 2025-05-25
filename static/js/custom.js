/*==================================
* Author        : "ThemeSine"
* Template Name : Khanas HTML Template
* Version       : 1.0
==================================== */
/*=========== TABLE OF CONTENTS ===========
1. Scroll To Top 
2. Smooth Scroll spy
3. Progress-bar
4. owl carousel
5. welcome animation support
======================================*/

$(document).ready(function () {
    "use strict";
    initializeScrollToTop();
    initializeSmoothScrollSpy();
    initializeProgressBar();
    initializeOwlCarousel();
    initializeWelcomeAnimation();
    fetchAboutUsText();
    initializeLoadingBar();
    checkAndShowLoadingBarOnDataPage();

});


// 1. Scroll To Top
function initializeScrollToTop() {
    $(window).on('scroll', function () {
        if ($(this).scrollTop() > 600) {
            $('.return-to-top').fadeIn();
        } else {
            $('.return-to-top').fadeOut();
        }
    });

    $('.return-to-top').on('click', function () {
        $('html, body').animate({
            scrollTop: 0
        }, 1500);
        return false;
    });
}

$(document).ready(function () {
    // Show/hide the button
    $(window).scroll(function () {
        if ($(this).scrollTop() > 100) {
            $('#scroll-Top').fadeIn();
        } else {
            $('#scroll-Top').fadeOut();
        }
    });
    // Scroll to top on click
    $('#scroll-top').click(function () {
        $("html, body").animate({ scrollTop: 0 }, 600);
        return false;
    });
});





// 2. Smooth Scroll spy
function initializeSmoothScrollSpy() {
    $('.header-area').sticky({
        topSpacing: 0
    });

    $('li.smooth-menu a').bind("click", function (event) {
        event.preventDefault();
        var anchor = $(this);
        var headerOffset = 80; // Adjust this value based on your header height
        $('html, body').stop().animate({
            scrollTop: $(anchor.attr('href')).offset().top - headerOffset // Add the offset
        }, 1200, 'easeInOutExpo');
    });

    $('body').scrollspy({
        target: '.navbar-collapse',
        offset: 80 // Match the header offset here
    });
}


// 3. Progress-bar
function initializeProgressBar() {
    var dataToggleTooTip = $('[data-toggle="tooltip"]');
    var progressBar = $(".progress-bar");
    if (progressBar.length) {
        progressBar.appear(function () {
            dataToggleTooTip.tooltip({
                trigger: 'manual'
            }).tooltip('show');
            progressBar.each(function () {
                var each_bar_width = $(this).attr('aria-valuenow');
                $(this).width(each_bar_width + '%');
            });
        });
    }
}


// 4. owl carousel
function initializeOwlCarousel() {
    $('#client').owlCarousel({
        items: 7,
        loop: true,
        smartSpeed: 1000,
        autoplay: true,
        dots: false,
        autoplayHoverPause: true,
        responsive: {
            0: { items: 2 },
            415: { items: 2 },
            600: { items: 4 },
            1199: { items: 4 },
            1200: { items: 7 }
        }
    });

    $('.play').on('click', function () {
        owl.trigger('play.owl.autoplay', [1000]);
    });

    $('.stop').on('click', function () {
        owl.trigger('stop.owl.autoplay');
    });
}


//  5. welcome animation support

function initializeWelcomeAnimation() {
    $(window).load(function () {
        $(".header-text h2,.header-text p").removeClass("animated fadeInUp").css({ 'opacity': '0' });
        $(".header-text a").removeClass("animated fadeInDown").css({ 'opacity': '0' });
    });

    $(window).load(function () {
        $(".header-text h2,.header-text p").addClass("animated fadeInUp").css({ 'opacity': '0' });
        $(".header-text a").addClass("animated fadeInDown").css({ 'opacity': '0' });
    });
}


// 6. fetch about us text
function fetchAboutUsText() {
    $.get("/static/AboutUs.txt")
        .done(function (data) {
            console.log("Fetched data:", data);
            $("#about-content").html(data); // Use jQuery to set the content
        })
        .fail(function (error) {
            console.error("Error loading About Us content:", error);
            $("#about-content").html("<p>Unable to load content.</p>");
        });
}


// 7. LOADING BAR - SHAKED
// This function initializes the loading bar and sets up the form submission and cancel button functionality
function initializeLoadingBar() {
    const sessionId = Date.now().toString(); // Use a timestamp as a unique session ID

    setupFormSubmission(sessionId);
    setupCancelButton(sessionId);
}

function checkAndShowLoadingBarOnDataPage() {
    if (window.location.pathname === "/data") {
        const sessionId = sessionStorage.getItem("sessionId");
        if (sessionId) {
            // Check progress status before showing/loading bar
            $.ajax({
                url: "/progress",
                method: "GET",
                success: function (response) {
                    updateSummary(); // Update summary immediately
                    if (response.status === 1) { // Only if running
                        showLoadingBar();
                        startPollingProgress(sessionId);
                    } else {
                        hideLoadingBar();
                    }
                },
                error: function (error) {
                    console.error("Error checking progress:", error);
                }
            });
        }
    }
}

// This function sets up the form submission event handler
// It prevents the default form submission, shows the loading bar, and starts polling for progress
function setupFormSubmission(sessionId) {
    $("#infoForm").on("submit", function (event) {
        event.preventDefault(); // Prevent the default form submission

        // Generate a new session ID for each submission
        sessionId = Date.now().toString();
        sessionStorage.setItem("sessionId", sessionId);

        // Collect form data
        const formData = {
            domain: $("#domain").val(),
            country: $("#country").val(),
            company: $("#company").val(),
            session_id: sessionId
        };

        // Make an AJAX request to start loading the data
        $.ajax({
            url: "/load_data", // Endpoint to load data
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify(formData),
            success: function (response) {
                console.log("Data loading started:", response);
                window.location.href = "/data"; // Redirect to the /data page
            },
            error: function (error) {
                console.error("Error starting data load:", error);
                hideLoadingBar();
                alert("Failed to start data loading. Please try again.");
            }
        });
    });
}


// This function shows the loading bar and initializes its state
// It also shows the cancel button and loading circle
function showLoadingBar() {
    $("#loading-spinner").show(); // Show the spinner
    $("#loading-bar-container").show();
    $("#loading-bar").css("width", "0%"); // Reset the progress bar
    $("#loading-percentage").text("0%"); // Reset the percentage text
    $("#cancelButton").show(); // Show the Cancel button
    $("#loading-circle").show(); // Show the loading circle
    $("#task-description").show();
    $("#coffee-break-message").show(); // Show the coffee break message
}


// This function hides the loading bar and resets its state
// It also hides the cancel button and loading circle
function hideLoadingBar() {
    $("#loading-spinner").hide(); // Hide the spinner
    $("#loading-bar-container").hide();
    $("#loading-circle").hide(); // Hide the loading circle
    $("#cancelButton").hide(); // Hide the Cancel button
    $("#task-description").hide();
    $("#coffee-break-message").hide(); // Hide the coffee break message
}

// This function starts polling the progress endpoint every second
// It updates the loading bar width, percentage text, and task description based on the response
function startPollingProgress(sessionId) {
    const pollProgress = setInterval(() => {
        $.ajax({
            url: "/progress", // Endpoint to get progress
            method: "GET",
            success: function (response) {
                const progress = response.value; // Get the progress value (0-100)
                const task = response.task; // Get the current task description
                const status = response.status; // Get the status
                $("#loading-bar").css("width", progress + "%"); // Update the bar width
                $("#loading-percentage").text(progress + "%"); // Update the percentage text
                $("#task-description").text(task); // Update the task description

                if (status === 1) {
                    setInterval(updateSummary, 5000); // Update summary every 5 seconds
                }

                if (progress >= 100) {
                    clearInterval(pollProgress); // Stop polling when progress reaches 100%

                    // Keep the completed bar visible for 1 second before hiding it
                    setTimeout(() => {
                        hideLoadingBar();
                        // // Redirect to the /data page
                        // window.location.href = "/data";
                    }, 1000); // Delay of 1 second
                }
            },
            error: function (error) {
                console.error("Error fetching progress:", error);
            }
        });
    }, 1000); // Poll every 1000ms (1 second)
}

// This function sets up the cancel button event handler
// It sends a cancel request to the server and hides the loading bar
function setupCancelButton(sessionId) {
    $("#cancelButton").on("click", function () {
        $.ajax({
            url: "/cancel",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ session_id: sessionId }),
            success: function (response) {
                console.log(response.message);
                hideLoadingBar();
                alert("Request canceled.");
            },
            error: function (error) {
                console.error("Error canceling the process:", error);
                alert("Failed to cancel the process. Please try again.");
            }
        });
    });
}

function updateSummary() {
    $.ajax({
        url: "/data_json",
        method: "GET",
        success: function (data) {
            // Update counters
            $("#summary-email-count").text(data.email_count);
            $("#summary-ips-count").text(data.ips_count);
            $("#summary-employees-count").text(data.employees_count);
            $("#summary-domains-count").text(data.domains_count);

            // Update SPF, DKIM, DMARC, Vulnerabilities
            updateSummaryChips(data.dkimdmarc, data.ips);
        }
    });
}

const chipSectionState = {
    "#spf-missing-list": false,
    "#dkim-missing-list": false,
    "#dmarc-missing-list": false,
    "#vuln-list": false
};

const expandedVulnSet = new Set();

// Helper to update chips for SPF, DKIM, DMARC, Vulnerabilities
function updateSummaryChips(dkimdmarc, ips) {
    // SPF
    let spf_missing = dkimdmarc.filter(r => r.SPF === "No SPF record found").map(r => r.domain || "N/A");
    updateChipSection("#spf-missing-list", spf_missing, "No missing SPF records");

    // DKIM
    let dkim_missing = dkimdmarc.filter(r => r.DKIM === "No DKIM record found").map(r => r.domain || "N/A");
    updateChipSection("#dkim-missing-list", dkim_missing, "No missing DKIM records");

    // DMARC
    let dmarc_missing = dkimdmarc.filter(r => r.DMARC === "No DMARC record found").map(r => r.domain || "N/A");
    updateChipSection("#dmarc-missing-list", dmarc_missing, "No missing DMARC records");

    // Vulnerabilities
    let vulnerabilities = (ips || []).filter(ip => ip.vulns).map(ip => ip.vulns);
    updateChipSection("#vuln-list", vulnerabilities, "No vulnerabilities found", true);
}

function updateChipSection(selector, items, emptyText, isVuln) {
    let container = $(selector);
    if (!container.length) return;

    // Use the global state
    const wasExpanded = chipSectionState[selector] || false;

    container.empty();
    if (items.length === 0) {
        container.append(`<span>✅ ${emptyText}</span>`);
    } else {
        items.forEach((item, idx) => {
            let hiddenClass = (idx >= 5 && !wasExpanded) ? "hidden" : "";
            if (isVuln) {
                const isExpanded = expandedVulnSet.has(item);
                container.append(
                    `<div class="chip ${hiddenClass}" onclick="toggleFullVuln(this, '${item.replace(/'/g, "\\'")}')">
                        <span class="vuln-short" style="display:${isExpanded ? 'none' : 'inline'};">${item.substring(0, 13)}...</span>
                        <span class="vuln-full" style="display:${isExpanded ? 'inline' : 'none'};">${item}</span>
                    </div>`
                );
            } else {
                container.append(`<div class="chip ${hiddenClass}">${item}</div>`);
            }
        });
        if (items.length > 5) {
            const btnText = wasExpanded ? "Show less" : "Show more";
            container.append(`<button class="button-inline" onclick="toggleVisibility(this, '${selector}')" data-expanded="${wasExpanded}">${btnText}</button>`);
        }
    }
}


function toggleVisibility(button, selector) {
    const container = button.parentElement;
    const hiddenItems = container.querySelectorAll('.chip.hidden');
    const isHidden = hiddenItems.length > 0 && (hiddenItems[0].style.display === 'none' || hiddenItems[0].style.display === '');

    hiddenItems.forEach(item => {
        item.style.display = isHidden ? 'inline-flex' : 'none';
    });

    button.textContent = isHidden ? 'Show less' : 'Show more';

    // Update the global state
    chipSectionState[selector] = isHidden;
}

function toggleFullVuln(element, vulnKey) {
    const shortSpan = element.querySelector('.vuln-short');
    const fullSpan = element.querySelector('.vuln-full');
    const isNowExpanded = shortSpan.style.display !== 'none';

    if (isNowExpanded) {
        shortSpan.style.display = 'none';
        fullSpan.style.display = 'inline';
        expandedVulnSet.add(vulnKey);
    } else {
        shortSpan.style.display = 'inline';
        fullSpan.style.display = 'none';
        expandedVulnSet.delete(vulnKey);
    }
}

// Poll for progress status every 2 seconds
function checkProgressAndRedirect() {
    fetch("/progress")
        .then(response => response.json())
        .then(data => {
            if (data.status === 0) {
                // Data is finished loading, redirect to /data
                window.location.href = "/data";
            } else {
                // Continue polling until status is 0
                setTimeout(checkProgressAndRedirect, 2000);
            }
        })
        .catch(error => {
            console.error("Error fetching progress:", error);
            setTimeout(checkProgressAndRedirect, 2000); // Retry after delay
        });
}

// Start polling after page load
document.addEventListener("DOMContentLoaded", function() {
    checkProgressAndRedirect();
});