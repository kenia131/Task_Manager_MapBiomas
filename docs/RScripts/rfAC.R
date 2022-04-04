library("randomForest")
library("raster")
library("rgdal")
library("grid")
library("gridExtra")
library('rpart')
library('rpart.plot')
library('tree')
library('rpart.utils')
library('corrplot')
library('rfUtilities')
library('foreach')
library('doSNOW')
library('Boruta')

set.seed(1234567890)

setwd('/disco4/mapbiomas')

IMAGES_DIR   <- 'data/images/'
TRAINING_DIR <- 'data/training/'
OUTPUT_DIR   <- 'data/output/'

YEARS <- c(2010)
PREFIX <- 'L5_T1_TOA'
#WRS <- c('220069', '220073', '230069', '227062', '221065', '218065', '218068', '225072', '225075')
WRS <- c('219075', '232058', '226069', '217066', '223077', '223080', '222072', '222075', '222079')
POINTS_REFERENCE <- '_ifac_2010_pnt_10000'
POINTS <- c(10000)

PERIODS <- c('WET', 'DRY')
REDUCERS <- c('qmo', 'max', 'min', 'median', 'stdDev')
BANDS <- c('BLUE', 'GREEN', 'RED', 'NIR', 'SWIR1', 'SWIR2', 'TIR1', 'TIR2', 'EVI2', 'NDWI', 'CAI')
IGNORE_BANDS <- c('TIR2')
IGNORE_VARIABLES <- c()

#IGNORE_VARIABLES <- c("ALL_cei_BLUE", "ALL_cei_GREEN", "ALL_cei_SWIR1", "ALL_cei_TIR1", "DRY_max_BLUE", "DRY_min_BLUE", "DRY_qmo_BLUE",
#"DRY_qmo_GREEN", "DRY_qmo_RED", "DRY_qmo_SWIR1", "DRY_qmo_TIR1", "DRY_stdDev_BLUE", "DRY_stdDev_CAI", "DRY_stdDev_GREEN",
#"DRY_stdDev_NIR", "DRY_stdDev_RED", "DRY_stdDev_TIR1", "WET_max_BLUE", "WET_max_GREEN", "WET_median_NIR", "WET_min_TIR1",
#"WET_qmo_BLUE", "WET_qmo_CAI", "WET_qmo_GREEN", "WET_qmo_RED", "WET_qmo_SWIR2", "WET_qmo_TIR1", "WET_stdDev_BLUE","WET_stdDev_GREEN")

#IGNORE_VARIABLES <- c("ALL_cei_BLUE", "ALL_cei_CAI", "ALL_cei_GREEN", "ALL_cei_RED", "ALL_cei_SWIR1", "ALL_cei_SWIR2", "ALL_cei_TIR1", "DRY_max_BLUE",
#"DRY_max_EVI2", "DRY_max_GREEN", "DRY_max_NIR", "DRY_max_TIR1", "DRY_median_CAI", "DRY_median_NIR", "DRY_median_TIR1", "DRY_min_BLUE",
#"DRY_min_CAI", "DRY_min_GREEN", "DRY_min_NIR", "DRY_min_SWIR1", "DRY_min_TIR1", "DRY_qmo_BLUE", "DRY_qmo_EVI2", "DRY_qmo_GREEN", "DRY_qmo_NIR", "DRY_qmo_RED", "DRY_qmo_SWIR1", "DRY_qmo_SWIR2",
#"DRY_qmo_TIR1", "DRY_stdDev_BLUE", "DRY_stdDev_CAI", "DRY_stdDev_EVI2", "DRY_stdDev_GREEN", "DRY_stdDev_NIR", "DRY_stdDev_RED", "DRY_stdDev_SWIR2", "DRY_stdDev_TIR1",
#"WET_max_BLUE", "WET_max_GREEN", "WET_max_NIR", "WET_median_BLUE", "WET_median_EVI2", "WET_median_NIR", "WET_median_TIR1", "WET_min_BLUE", "WET_min_NIR", "WET_min_RED", "WET_min_SWIR2", "WET_min_TIR1",
#"WET_qmo_BLUE", "WET_qmo_CAI", "WET_qmo_GREEN", "WET_qmo_NDWI", "WET_qmo_RED", "WET_qmo_SWIR2", "WET_qmo_TIR1", "WET_stdDev_BLUE", "WET_stdDev_GREEN", "WET_stdDev_NIR")


mb.loadImages <- function(dir, card, periods, reducers, bands, ignore_bands){ 
band_names <- c()
  ignore_band_names <- c()

  images <- stack()

  image_wet_qmo = NULL
  image_dry_min = NULL

  for (p in periods){
    for (r in reducers){
      for (b in bands){
        prefix <- paste(p, r, b, sep='_')
        band_names <- c(band_names, prefix)
        if( b %in% ignore_bands ){
          ignore_band_names <- c(ignore_band_names, prefix)
        }
      }
      filename <- paste0(paste(paste0(dir, card), p, r, sep = '_'), '.tif')
      print(filename)
      image = brick(filename)
      images <- stack(images, image)
      if (p == 'WET' && r == 'qmo'){
        image_wet_qmo <- image
      }
      if (p == 'DRY' && r == 'min'){
        image_dry_min <- image
      }
    }
  }

  print("Calculating CEI...")
  cei <- 1000000*(image_wet_qmo - image_dry_min) / (1000000+image_wet_qmo + 1000000+image_dry_min)
  for (b in bands){
    prefix <- paste('ALL', 'cei', b, sep='_')
    band_names <- c(band_names, prefix)
    if( b %in% ignore_bands ){
      ignore_band_names <- c(ignore_band_names, prefix)
    }
  }
  images <- stack(images, cei)
  print("CEI calculed!")

  names(images) <- band_names
  desired_bands <- band_names[ ! band_names %in% ignore_band_names ]
  return (images[[desired_bands]])
}
print("asdsad")
mb.loadTrainingByWRS <- function(wrs, dir, POINTS_REFERENCE, format='.shp'){
  filename <- paste0(dir, wrs, POINTS_REFERENCE, format)
  print(filename)
  training <- shapefile(filename)
  return(training)
}

mb.extract <- function(images, training, nsample=NULL){
  if(!is.null(nsample)){
    nsample <- round(runif(n = nsample, min = 1, max = nrow(training)))
    training <-  training[nsample,]
  }
  data <- raster::extract(images, training, df=TRUE)
  data$desc <- as.factor(training$class)
  return(data)
}

mb.calc.collinearVariables <- function(model_variables, n, p){
  #analise das bandas 'ruins' com problema de multcolinearidade
  mcollinear <- multi.collinear(model_variables, perm = TRUE, leave.out = TRUE, n = n, p = p, na.rm = TRUE)
  mcollinear_frame <- data.frame(mcollinear)
  mcollinear_frame <- mcollinear_frame[with(mcollinear_frame, order(-frequency)),]
  return(mcollinear_frame)
}

mb.calc.modelSel <- function(model_variables, response_variables){
  #analise das bandas boas... selecionadas para a modelagem
  selection = rf.modelSel(model_variables, response_variables, imp.scale = "mir", r = c(0.25, 0.5, 0.75), final.model = FALSE, seed = NULL, parsimony = NULL)
  selection$importance$vars <- rownames(selection$importance)
  selection$importance <- selection$importance[with(selection$importance, order(-imp)),]
  return(selection)
}

mb.calc.importanceFrequence <- function(rf, p=0.3, plot=FALSE){
  #análise das floresta de arvores q o ramdomforest criou para checar se as bandas mais importantes foram as mais selecionadas pelas arvores
  rf_impfreq <- rf.imp.freq(rf, p = p, plot = plot)
  rf_impfreq$importance <- data.frame(rf_impfreq$importance)
  rf_impfreq$importance <- rf_impfreq$importance[with(rf_impfreq$importance, order(-MeanDecreaseAccuracy)),]
  rf_impfreq$frequency <- rf_impfreq$frequency[with(rf_impfreq$frequency, order(-var.freq)),]
  return(rf_impfreq)
}

mb.calc.accuracy <- function(predicted, observed){
  accuracy <- accuracy(predicted, observed)
  return(accuracy)
}

mb.plot.randomForest <- function(rf, model_variables, response_variables){
  collinearVariables  <- mb.calc.collinearVariables(model_variables, 100, 0.05)
  modelSel            <- mb.calc.modelSel(model_variables, response_variables)
  importanceFrequence <- mb.calc.importanceFrequence(rf, p=0.3, plot = FALSE)
  accuracy            <- mb.calc.accuracy(rf$predicted, response_variables)
  writeLines("\n ************ RF Basic ****************** \n")
  print(rf)
  writeLines("\n ********** RF Importance and Frequence (importance(rf) ****************** \n")
  print(importanceFrequence)
  writeLines("\n ************ RF Collinear Variables ****************** \n")
  print(collinearVariables)
  writeLines("\n ************ RF Selection model ****************** \n")
  print(modelSel)
  writeLines("\n ************ RF Accuracy ****************** \n")
  print(accuracy)
  plot(modelSel, imp = "sel")
}

mb.plot.rpart <- function(rp){
  writeLines("\n ************ Rpart ****************** \n")
  print(rp)
  writeLines("\n ************ Rpart CP *************** \n")
  printcp(rp)
  rpart.plot(x=rp)
}

mb.plot.tree <- function(tree){
  writeLines("\n ************ Tree ******************* \n")
  print(tree)
  writeLines("\n **********Tree Summary ************** \n")
  print(summary(tree))
}

mb.plot.rasterStack <- function(rasterStack){
  for(layer in as.list(rasterStack)){
    color <- gray.colors(255, start = 0, end = 1, gamma = 2, alpha = NULL)
    plot(layer, xlab=toString(names(layer)), col = color)
  }
}

mb.plot.correlationMatrix <- function(cor_variables, method="ellipse", type="lower"){
  correlation <- corrplot(cor(cor_variables), method = method, type = type,tl.cex = 0.3, tl.col = "indianred4", order="hclust", sig.level = 0.01)
  return(correlation)
}

mb.processWRS <- function(w){
  for(y in YEARS){
    card_name<- paste(PREFIX, w, y, sep = '_') #L5_T1_TOA_200069_2007

    images <- mb.loadImages(IMAGES_DIR, card_name, PERIODS, REDUCERS, BANDS, IGNORE_BANDS)
    print("Images carregadas!")
    print( with(images, which(!(names(images) %in% IGNORE_VARIABLES  )))  )
    images <- images[[with(images, which(!(names(images) %in% IGNORE_VARIABLES  )))]]
    print(names(images))
    training <- mb.loadTrainingByWRS(w, TRAINING_DIR, POINTS_REFERENCE)
    print("Treinamento carregado!")

    #pdf(paper="a4", file = paste0(OUTPUT_DIR, card_name,"_", "VARIABLES.pdf"))
    #mb.plot.rasterStack(images)
    #dev.off()

    for(p in POINTS){
      roi_data <- mb.extract(images, training, p)
      roi_data_tree <- mb.extract(images, training, 200)

      model_variables <- roi_data[,names(images)]
      response_variables <- roi_data$desc
      
      
      f <- eval( parse(text = paste('desc', paste(names(images), collapse=" + ") , sep=' ~ '))) # formula RandomForest
      roi_data.rf <- randomForest(f, data=roi_data, ntree=5000, importance=TRUE, proximity=TRUE, do.trace=T)
      roi_data.rp <- rpart(f, data=roi_data, method = 'class')
      roi_data.rpt <- tree(f, data=roi_data_tree, split = 'gini')
      roi_data.bor <- Boruta(f, data=roi_data, doTrace=2)

      pdf(paper="a4", file = paste0(OUTPUT_DIR, card_name,"_", POINTS_REFERENCE, toString(p),".pdf"))
      sink(file = paste0(OUTPUT_DIR, card_name,"_", POINTS_REFERENCE, toString(p), ".txt"))
	
      #plotRGB(stack(images$WET_qmo_NIR, images$WET_qmo_SWIR1, images$WET_qmo_RED), scale = 10000, zlim=c(0, 10000))
	
	
      tryCatch({
	mb.plot.randomForest(roi_data.rf, model_variables, response_variables)
      })
      tryCatch({
      	mb.plot.rpart(roi_data.rp)
      })
      tryCatch({
      	mb.plot.tree(roi_data.rpt)
      })
      
      writeLines("\n ************ Boruta ******************* \n")
      plot(roi_data.bor)
      print(roi_data.bor)
      print(cbind(names(roi_data.bor$finalDecision), as.character(roi_data.bor$finalDecision)))      

      for (period in PERIODS){
        mb.plot.correlationMatrix(model_variables[,grep(pattern = period, names(images))])
      }
      for (band in BANDS[!BANDS %in% IGNORE_BANDS]){
        mb.plot.correlationMatrix(model_variables[,grep(pattern = band, names(images))])
      }
      for (reducer in REDUCERS){
        mb.plot.correlationMatrix(model_variables[,grep(pattern = reducer, names(images))])
      }

      sink()
      dev.off()
    }
  }
}

cluster <- makeCluster(10, outfile = 'data/mapbiomas.log')
registerDoSNOW(cluster)

#for(wrs in WRS){
#	mb.processWRS(wrs)
#}

foreach (wrs=WRS, .packages = c("randomForest", "rgdal", "grid", "gridExtra", "rpart", "rpart.plot", "tree", "rpart.utils", "corrplot", "rfUtilities", "raster", "Boruta", "doSNOW") ) %dopar% {  
      mb.processWRS(wrs)
}

#save.image(file = 'environment.RData')
#load(file = 'environment.RData')

#plot(images$L5_T1_TOA_221065_2007_WET_min.10)

# Predict!

# image_class <- images
# names(image_class) <- bands
# image_pred <- predict(image_class, model=rf, na.rm=T)
#
# colors <- c(rgb(0, 150, 0, maxColorValue=255),  # Forest
#             rgb(0, 0, 255, maxColorValue=255),  # Water
#             rgb(0, 255, 0, maxColorValue=255),  # Herbaceous
#             rgb(160, 82, 45, maxColorValue=255),  # Barren
#             rgb(255, 0, 0, maxColorValue=255))  # Urban
#
# #plotRGB(image_pred, r=4, g=5, b=3, stretch="lin")ROOT_DIR
# plot(image_pred, col=colorRampPalette(c("red", "white", "blue"))(255))

# pdf:
# imagem
# rpart plot
# tree plot + text
# tree print  (capture.output())
# rf varImpPlot
# rf proximity

# txt
# nome da imagem
# nome dos pontos
# CART(rpart)
# rpart print
# rpart printcp
# CART(tree)
# tree print
# tree summary
# RANDOMFOREST
# rf print
# rf importance (ordenado)
