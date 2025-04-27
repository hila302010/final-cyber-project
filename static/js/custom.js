$(document).ready(function(){
	"use strict";
    
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


	// 1. Scroll To Top
	$(window).on('scroll', function() {
			if ($(this).scrollTop() > 600) {
					$('.return-to-top').fadeIn();
			} else {
					$('.return-to-top').fadeOut();
			}
	});
	$('.return-to-top').on('click', function() {
			$('html, body').animate({
					scrollTop: 0
			}, 1500);
			return false;
	});

	// 2. Smooth Scroll spy
	$('.header-area').sticky({
			topSpacing: 0
	});

	$('li.smooth-menu a').bind("click", function(event) {
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



	// 3. Progress-bar
	
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
	
	// 4. owl carousel
	
		// i. client (carousel)
		
			$('#client').owlCarousel({
				items:7,
				loop:true,
				smartSpeed: 1000,
				autoplay:true,
				dots:false,
				autoplayHoverPause:true,
				responsive:{
						0:{
							items:2
						},
						415:{
							items:2
						},
						600:{
							items:4

						},
						1199:{
							items:4
						},
						1200:{
							items:7
						}
					}
				});
				
				
				$('.play').on('click',function(){
					owl.trigger('play.owl.autoplay',[1000])
				})
				$('.stop').on('click',function(){
					owl.trigger('stop.owl.autoplay')
				})


    // 5. welcome animation support

        $(window).load(function(){
        	$(".header-text h2,.header-text p").removeClass("animated fadeInUp").css({'opacity':'0'});
            $(".header-text a").removeClass("animated fadeInDown").css({'opacity':'0'});
        });

        $(window).load(function(){
        	$(".header-text h2,.header-text p").addClass("animated fadeInUp").css({'opacity':'0'});
            $(".header-text a").addClass("animated fadeInDown").css({'opacity':'0'});
        });

				// 6. fetch about us text
				$(document).ready(function () {
					$.get("/static/AboutUs.txt")
							.done(function (data) {
									console.log("Fetched data:", data);
									$("#about-content").html(data); // Use jQuery to set the content
							})
							.fail(function (error) {
									console.error("Error loading About Us content:", error);
									$("#about-content").html("<p>Unable to load content.</p>");
							});
			});
				//LOADING BAR - SHAKED
				$(document).ready(function () {
					
					const sessionId = Date.now().toString(); // Use a timestamp as a unique session ID
					
					$("#infoForm").on("submit", function (event) {
						event.preventDefault(); // Prevent the default form submission
				
						// Show the loading bar container
						$("#loading-bar-container").show();
						$("#loading-bar").css("width", "0%"); // Reset the progress bar
						$("#loading-percentage").text("0%"); // Reset the percentage text
						$("#cancelButton").show(); // Show the Cancel button
						$("#loading-circle").show(); // Show the loading circle
						$("#task-description").show();



						// Collect form data
						const formData = {
							domain: $("#domain").val(),
							country: $("#country").val(),
							company: $("#company").val(),
							session_id: sessionId
						};
				
						// Start polling the progress endpoint
						const pollProgress = setInterval(() => {
							$.ajax({
								url: "/progress", // Endpoint to get progress
								method: "GET",
								success: function (response) {
									const progress = response.value; // Get the progress value (0-100)
									const task = response.task; // Get the current task description
									$("#loading-bar").css("width", progress + "%"); // Update the bar width
									$("#loading-percentage").text(progress + "%"); // Update the percentage text
									// Update the task description
									$("#task-description").text(task);

									if (progress >= 100) {
										clearInterval(pollProgress); // Stop polling when progress reaches 100%
				
										// Keep the completed bar visible for 1 second before hiding it
										setTimeout(() => {
											$("#loading-bar-container").hide();
											$("#loading-circle").hide(); // Hide the loading circle
				                            $("#cancelButton").hide(); // Hide the Cancel button
											$("#task-description").hide();

											// Redirect to the /data page
											window.location.href = "/data";
										}, 1000); // Delay of 1 second
									}
								},
								error: function (error) {
									console.error("Error fetching progress:", error);
								}
							});
						}, 1000); // Poll every 1000ms (1 second)
				
						// Make an AJAX request to start loading the data
						$.ajax({
							url: "/load_data", // Endpoint to load data
							method: "POST",
							contentType: "application/json",
							data: JSON.stringify(formData),
							success: function (response) {
								console.log("Data loading started:", response);
							},
							error: function (error) {
								console.error("Error starting data load:", error);
								$("#loading-bar-container").hide();
								$("#loading-circle").hide(); // Hide the loading circle
								$("#cancelButton").hide(); // Hide the Cancel button
								$("#task-description").hide();
								alert("Failed to start data loading. Please try again.");
							}
						});
					});
					// Handle cancel button click
					$("#cancelButton").on("click", function () {
						$.ajax({
							url: "/cancel",
							method: "POST",
							contentType: "application/json",
							data: JSON.stringify({ session_id: sessionId }),
							success: function (response) {
								console.log(response.message);
								$("#loading-bar-container").hide(); // Hide the loading bar
								$("#loading-circle").hide(); // Hide the loading circle
								$("#cancelButton").hide(); // Hide the Cancel button
								$("#task-description").hide(); // Hide the task description
								alert("Request canceled.");
							},
							error: function (error) {
								console.error("Error canceling the process:", error);
								alert("Failed to cancel the process. Please try again.");
							}
						});
					});

				});
});	
	