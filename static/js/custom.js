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

				// 7. fetch the result from submit button
				// Ensure that the DOM is fully loaded before attaching event handlers
				$(document).ready(function () {
							$("#infoForm").on("submit", function (event) {
									event.preventDefault(); // Prevent the default form submission
					
									const formData = $(this).serialize(); // Serialize form data
					
									// Show the loading bar
									$("#loading").show();

									    // Simulate a delay of 10 seconds before redirecting to data.html
											setTimeout(function () {
												window.location.href = "data.html"; // Redirect to data.html
										}, 10000);

									/*$("#result").html(""); // Clear previous results
					
									$.ajax({
											url: "/submit",
											type: "POST",
											data: formData,
											success: function (response) {
												console.log("Response:", response); // Log the response to inspect its structure
										
												// Check if the response is an array
												if (Array.isArray(response)) {
														let resultHtml = `
																<h2>Networks DB to Shodan Results</h2>
																<table>
																		<thead>
																				<tr>
																						<th>Address</th>
																						<th>Port</th>
																						<th>Vulnerabilities</th>
																						<th>Organization</th>
																						<th>Country</th>
																						<th>City</th>
																						<th>IP</th>
																						<th>Domains</th>
																						<th>Hostnames</th>
																				</tr>
																		</thead>
																		<tbody>
														`;
										
														// Iterate over the response array and create table rows
														response.forEach(row => {
																resultHtml += `
																		<tr>
																				<td>${row.address || "N/A"}</td>
																				<td>${row.port || "N/A"}</td>
																				<td>${row.vulns || "N/A"}</td>
																				<td>${row.org || "N/A"}</td>
																				<td>${row.country_name || "N/A"}</td>
																				<td>${row.city || "N/A"}</td>
																				<td>${row.ip_str || "N/A"}</td>
																				<td>${row.domains || "N/A"}</td>
																				<td>${row.hostnames || "N/A"}</td>
																		</tr>
																`;
														});
										
														resultHtml += `
																		</tbody>
																</table>
														`;
										
														// Update the result div with the generated HTML
														$("#result").html(resultHtml);
												} else {
														// If the response is not an array, display it as plain text
														$("#result").html(`<pre>${JSON.stringify(response, null, 2)}</pre>`);
												}
										},
											error: function (xhr, status, error) {
													console.error("Error:", error);
													$("#result").html("An error occurred. Please try again.");
											},
											complete: function () {
													// Hide the loading bar after the request is complete
													$("#loading").hide();
											}
									});*/
							});
					});


});	
	