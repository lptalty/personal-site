module.exports = function (eleventyConfig) {
  eleventyConfig.addFilter("dateFormat", function (date, format) {
    const d = new Date(date);
    const months = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December",
    ];
    const monthsShort = [
      "Jan",
      "Feb",
      "Mar",
      "Apr",
      "May",
      "Jun",
      "Jul",
      "Aug",
      "Sep",
      "Oct",
      "Nov",
      "Dec",
    ];

    if (format === "short") {
      return `${monthsShort[d.getMonth()]} ${d.getFullYear()}`;
    } else if (format === "iso") {
      return d.toISOString().split("T")[0];
    } else {
      return `${months[d.getMonth()]} ${d.getDate()}, ${d.getFullYear()}`;
    }
  });

  eleventyConfig.addCollection("essays", function (collectionApi) {
    return collectionApi.getFilteredByTag("essay").filter((item) => {
      const url = item.url;
      const parts = url.split("/").filter(Boolean);
      return parts.length > 2;
    });
  });

  eleventyConfig.addPassthroughCopy("src/css");
  eleventyConfig.addPassthroughCopy("src/favicon-32x32.png");

  eleventyConfig.addWatchTarget("src/css/");

  return {
    dir: {
      input: "src",
      output: "_site",
      includes: "_includes",
    },
  };
};
