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
    // initializeLoadingBar();

    // Only initialize loading bar logic on the relevant pages
    if (window.location.pathname === "/") {
        // On index.html, set up form and loading bar
        initializeLoadingBar();
    } else if (window.location.pathname === "/data") {
        // On data.html, just show and update the loading bar if progress < 100%
        showLoadingBar();
        // You need to get the sessionId from the server or sessionStorage
        // For example, if you store it in sessionStorage:
        const sessionId = sessionStorage.getItem("sessionId");
        if (sessionId) {
            startPollingProgress(sessionId);
        }
    }
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

// This function sets up the form submission event handler
// It prevents the default form submission, shows the loading bar, and starts polling for progress
function setupFormSubmission(sessionId) {
    $("#infoForm").on("submit", function (event) {
        event.preventDefault(); // Prevent the default form submission

        // // Show the loading bar container
        // showLoadingBar();

         // Store sessionId for use on /data page
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
                // Show the loading bar container
                showLoadingBar();

                // Start polling the progress endpoint
                startPollingProgress(sessionId);
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
                $("#loading-bar").css("width", progress + "%"); // Update the bar width
                $("#loading-percentage").text(progress + "%"); // Update the percentage text
                $("#task-description").text(task); // Update the task description

                if (window.location.pathname === "/data" && progress < 100) {
                    setTimeout(function () {
                        window.location.reload();
                    }, 5000);
                }
                else if (progress >= 100) {
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