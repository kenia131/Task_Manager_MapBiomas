// set the path to the api.js script you copied to your GEE account:
var api = require('users/your_username/repository:utils/api.js');

/************* SETTINGS **************/

// set the output path for the classification results:
var outputCollection = 'users/your_username/MAPBIOMAS/C6/FOREST_PLANTATION/RESULTS/RAW';

// set the years you want to classify:
var years = [2015, 2016, 2017, 2018, 2019];

var offset = 2;

var cloudCover = 90;

// set the WRS (path and row) you want to classify:
var tiles = [[220, 76], [220, 75]];

var bands = [
  api.Band.GREEN,
  api.Band.RED,
  api.Band.NIR,
  api.Band.SWIR1,
  api.Band.SWIR2,
  api.Band.EVI2,
  api.Band.NDVI,
  api.Band.LAI
];

var reducers = [
  api.Reducer.QMO(api.Band.EVI2),
];

// set the periods for the region you want to classify
// more information about that you can read on the ATBD Forest Plantation Appendix
var periods = {
  'WET1': '(Y-1)-12-01,(Y)-01-31',
  'WET2': '(Y)-02-01,(Y)-03-31',
  'DRY1': '(Y)-04-01,(Y)-05-31',
  'DRY2': '(Y)-06-01,(Y)-07-31',
  'DRY3': '(Y)-08-01,(Y)-09-30',
  'WET3': '(Y)-10-01,(Y)-11-30',
};

var featureSpace = [
  'WET1_GREEN_qmo', 'WET1_RED_qmo', 'WET1_NIR_qmo', 'WET1_SWIR1_qmo', 'WET1_SWIR2_qmo', 'WET1_NDVI_qmo', 'WET1_LAI_qmo',
  'WET2_GREEN_qmo', 'WET2_RED_qmo', 'WET2_NIR_qmo', 'WET2_SWIR1_qmo', 'WET2_SWIR2_qmo', 'WET2_NDVI_qmo', 'WET2_LAI_qmo',
  'DRY1_GREEN_qmo', 'DRY1_RED_qmo', 'DRY1_NIR_qmo', 'DRY1_SWIR1_qmo', 'DRY1_SWIR2_qmo', 'DRY1_NDVI_qmo', 'DRY1_LAI_qmo',
  'DRY2_GREEN_qmo', 'DRY2_RED_qmo', 'DRY2_NIR_qmo', 'DRY2_SWIR1_qmo', 'DRY2_SWIR2_qmo', 'DRY2_NDVI_qmo', 'DRY2_LAI_qmo',
  'DRY3_GREEN_qmo', 'DRY3_RED_qmo', 'DRY3_NIR_qmo', 'DRY3_SWIR1_qmo', 'DRY3_SWIR2_qmo', 'DRY3_NDVI_qmo', 'DRY3_LAI_qmo',
  'WET3_GREEN_qmo', 'WET3_RED_qmo', 'WET3_NIR_qmo', 'WET3_SWIR1_qmo', 'WET3_SWIR2_qmo', 'WET3_NDVI_qmo', 'WET3_LAI_qmo',
]

// set the Image Collection you want to use to create the mosaics:
var imageCollection = ee.ImageCollection("LANDSAT/LC08/C01/T1_TOA");

// set the path to your reference map that will be used for sampling:
var reference = ee.Image("users/your_username/MAPBIOMAS/C6/FOREST_PLANTATION/REFERENCE_MAP");

var gridCollection = ee.FeatureCollection("users/agrosatelite_mapbiomas/COLECAO_6/GRIDS/BRASIL_COMPLETO");

var trainingSamples = 10000;

var randomForestTrees = 100;

/***************** END SETTINGS ******************/

/************* FUNCTIONS **************/

years.forEach(function (year) {
  tiles.forEach(function (wrs) {

    var filteredCollection = imageCollection
      .filterMetadata('WRS_PATH', 'equals', wrs[0])
      .filterMetadata('WRS_ROW', 'equals', wrs[1]);

    var roi = gridCollection
      .filterMetadata('PATH', "equals", wrs[0])
      .filterMetadata('ROW', "equals", wrs[1])
      .first()
      .geometry()
      .buffer(-4000);


    Map.addLayer(roi, {}, "ROI", false);

    var images = [];

    for (var period in periods) {
      var dates = periods[period];
      var filteredImages = ee.ImageCollection([]);

      for (var i = 0; i < offset; i++) {

        var apiImagesByPeriod = new api.ImageCollection(filteredCollection)
          .filterByPeriod(year, dates, offset, cloudCover)
          .applyBuffer(-4200)
          .removeClouds()
          .buildBands(bands);

        filteredImages = filteredImages.merge(apiImagesByPeriod.getEEImageCollection());
      }

      var apiFilteredImages = new api.ImageCollection(filteredImages);

      var image = apiFilteredImages
        .applyReducers(reducers)
        .getEEImage();

      image = image.rename(ee.Image(image).bandNames().map(
        function (band) {
          return ee.String(period).cat('_').cat(band);
        }
      ));

      images.push(image);
    }
    var mosaic = ee.Image.cat(images)
      .clip(roi)
      .unmask(null);

    var filename = "" + wrs[0] + wrs[1] + '_' + year;

    var mosaicFilename = filename + "_mosaic";

    Map.addLayer(mosaic, { bands: ['WET1_NIR_qmo', 'WET1_SWIR1_qmo', 'WET1_RED_qmo'], min: 100, max: 5000 }, mosaicFilename);

    mosaic = mosaic.select(featureSpace).multiply(10000);

    // Sampling //

    var train = mosaic.addBands(reference.select([0], ["class"])).unmask();
    var training = train.sample({
      'region': roi,
      'scale': 30,
      'numPixels': trainingSamples,
      'tileScale': 4
    });

    // Training // 

    var classifier = ee.Classifier
      .smileRandomForest(randomForestTrees)
      .train(training, 'class', featureSpace);

    // Classification //

    var classified = mosaic.classify(classifier)
      .set('year', year)
      .rename(['classification']);

    // Visualizing results //

    var referenceFilename = filename + "_reference";
    var classificationFilename = filename + "_classification";

    Map.addLayer(reference, { min: 0, max: 1 }, referenceFilename, false);
    Map.addLayer(classified, { min: 0, max: 1 }, classificationFilename, false);

    // Exporting Results //

    var filename = year + '_' + wrs[0] + '_' + wrs[1];

    Export.image.toAsset({
      image: classified.byte(),
      description: 'FOREST_PLANTATION_' + filename,
      assetId: outputCollection + '/' + filename,
      region: roi,
      scale: 30,
      maxPixels: 1.0E13
    });

  });
});


/************* END FUNCTIONS **************/