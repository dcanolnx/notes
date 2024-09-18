
#process_image_tag () {
#  echo ""
#  echo image $1 tag $2
#  manifests=$(curl -s -H 'Accept: application/vnd.oci.image.index.v1+json' -X GET http://docker-registry:5000/v2/$1/manifests/$2)
#  echo $manifests | jq
#  echo ""
#
#}
#
#for image in $(curl -s http://docker-registry:5000/v2/_catalog | jq -r '.repositories[]'); do
#  imageWithTags=$(curl -s http://docker-registry:5000/v2/$image/tags/list)
#  name=$(echo $imageWithTags | jq -r '.name')
#  #echo $imageWithTags | jq -r '.tags[]'
#  for tag in $(echo $imageWithTags | jq -r '.tags[]'); do
#  	process_image_tag $name $tag
#  done	
#done
#

#!/usr/bin/python3

def main():
    print("Hello World!")

if __name__ == "__main__":
    main()




